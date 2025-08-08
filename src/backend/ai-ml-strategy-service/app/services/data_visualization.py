"""
Data visualization service for creating interactive charts and data exploration.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.dataset import Dataset, AssetClass
from app.core.config import get_settings


class ChartGenerator:
    """Base class for chart generators."""
    
    def __init__(self, chart_type: str, description: str):
        self.chart_type = chart_type
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{chart_type}")
    
    def generate(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart from dataframe."""
        raise NotImplementedError("Subclasses must implement generate method")
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for this chart type."""
        raise NotImplementedError("Subclasses must implement get_config_schema method")


class TimeSeriesChartGenerator(ChartGenerator):
    """Generate time series charts for financial data."""
    
    def __init__(self):
        super().__init__(
            "time_series",
            "Time series line charts for price and volume data"
        )
    
    def generate(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate time series chart."""
        try:
            # Configuration
            x_column = config.get("x_column", "timestamp")
            y_columns = config.get("y_columns", ["close"])
            title = config.get("title", "Time Series Chart")
            height = config.get("height", 600)
            show_volume = config.get("show_volume", False)
            symbols = config.get("symbols", [])
            
            if x_column not in df.columns:
                raise ValueError(f"X column '{x_column}' not found in dataset")
            
            # Convert timestamp to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(df[x_column]):
                df[x_column] = pd.to_datetime(df[x_column])
            
            # Filter symbols if specified
            if symbols and "symbol" in df.columns:
                df = df[df["symbol"].isin(symbols)]
            
            # Create subplots
            subplot_count = 2 if show_volume and "volume" in df.columns else 1
            fig = make_subplots(
                rows=subplot_count,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=[title, "Volume"] if subplot_count > 1 else [title],
                row_heights=[0.7, 0.3] if subplot_count > 1 else [1.0]
            )
            
            # Color palette
            colors = px.colors.qualitative.Set1
            
            # Add price lines
            for i, y_col in enumerate(y_columns):
                if y_col not in df.columns:
                    continue
                
                if "symbol" in df.columns:
                    # Multi-symbol chart
                    for j, symbol in enumerate(df["symbol"].unique()):
                        symbol_data = df[df["symbol"] == symbol]
                        fig.add_trace(
                            go.Scatter(
                                x=symbol_data[x_column],
                                y=symbol_data[y_col],
                                mode="lines",
                                name=f"{symbol} - {y_col}",
                                line=dict(color=colors[j % len(colors)]),
                                hovertemplate=f"<b>{symbol}</b><br>" +
                                            f"{y_col}: %{{y:.4f}}<br>" +
                                            "Date: %{x}<br>" +
                                            "<extra></extra>"
                            ),
                            row=1, col=1
                        )
                else:
                    # Single series chart
                    fig.add_trace(
                        go.Scatter(
                            x=df[x_column],
                            y=df[y_col],
                            mode="lines",
                            name=y_col,
                            line=dict(color=colors[i % len(colors)]),
                            hovertemplate=f"{y_col}: %{{y:.4f}}<br>" +
                                        "Date: %{x}<br>" +
                                        "<extra></extra>"
                        ),
                        row=1, col=1
                    )
            
            # Add volume chart if requested
            if show_volume and "volume" in df.columns and subplot_count > 1:
                if "symbol" in df.columns:
                    for j, symbol in enumerate(df["symbol"].unique()):
                        symbol_data = df[df["symbol"] == symbol]
                        fig.add_trace(
                            go.Bar(
                                x=symbol_data[x_column],
                                y=symbol_data["volume"],
                                name=f"{symbol} - Volume",
                                marker_color=colors[j % len(colors)],
                                opacity=0.7,
                                showlegend=False
                            ),
                            row=2, col=1
                        )
                else:
                    fig.add_trace(
                        go.Bar(
                            x=df[x_column],
                            y=df["volume"],
                            name="Volume",
                            marker_color="lightblue",
                            opacity=0.7,
                            showlegend=False
                        ),
                        row=2, col=1
                    )
            
            # Update layout
            fig.update_layout(
                height=height,
                showlegend=True,
                hovermode="x unified",
                xaxis_rangeslider_visible=False
            )
            
            # Update y-axes
            fig.update_yaxes(title_text="Price", row=1, col=1)
            if subplot_count > 1:
                fig.update_yaxes(title_text="Volume", row=2, col=1)
            
            return {
                "success": True,
                "chart_type": "time_series",
                "plotly_json": fig.to_dict(),
                "config": {
                    "displayModeBar": True,
                    "modeBarButtonsToRemove": ["lasso2d", "select2d"]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Time series chart generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "x_column": {
                "type": "string",
                "default": "timestamp",
                "description": "Column to use for X-axis (time)"
            },
            "y_columns": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["close"],
                "description": "Columns to plot on Y-axis"
            },
            "title": {
                "type": "string",
                "default": "Time Series Chart",
                "description": "Chart title"
            },
            "height": {
                "type": "integer",
                "default": 600,
                "description": "Chart height in pixels"
            },
            "show_volume": {
                "type": "boolean",
                "default": False,
                "description": "Show volume subplot"
            },
            "symbols": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter to specific symbols"
            }
        }


class CandlestickChartGenerator(ChartGenerator):
    """Generate candlestick charts for OHLC data."""
    
    def __init__(self):
        super().__init__(
            "candlestick",
            "Candlestick charts for OHLC price data"
        )
    
    def generate(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate candlestick chart."""
        try:
            # Required columns
            required_cols = ["timestamp", "open", "high", "low", "close"]
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Configuration
            title = config.get("title", "Candlestick Chart")
            height = config.get("height", 600)
            show_volume = config.get("show_volume", False)
            symbol = config.get("symbol")
            
            # Convert timestamp to datetime
            if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            # Filter to specific symbol if requested
            if symbol and "symbol" in df.columns:
                df = df[df["symbol"] == symbol]
                title = f"{title} - {symbol}"
            
            # Create subplots
            subplot_count = 2 if show_volume and "volume" in df.columns else 1
            fig = make_subplots(
                rows=subplot_count,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=[title, "Volume"] if subplot_count > 1 else [title],
                row_heights=[0.7, 0.3] if subplot_count > 1 else [1.0]
            )
            
            # Add candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=df["timestamp"],
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name="OHLC",
                    increasing_line_color="green",
                    decreasing_line_color="red"
                ),
                row=1, col=1
            )
            
            # Add volume chart if requested
            if show_volume and "volume" in df.columns and subplot_count > 1:
                # Color volume bars based on price movement
                colors = ["green" if close >= open else "red" 
                         for close, open in zip(df["close"], df["open"])]
                
                fig.add_trace(
                    go.Bar(
                        x=df["timestamp"],
                        y=df["volume"],
                        name="Volume",
                        marker_color=colors,
                        opacity=0.7,
                        showlegend=False
                    ),
                    row=2, col=1
                )
            
            # Update layout
            fig.update_layout(
                height=height,
                xaxis_rangeslider_visible=False,
                showlegend=False
            )
            
            # Update y-axes
            fig.update_yaxes(title_text="Price", row=1, col=1)
            if subplot_count > 1:
                fig.update_yaxes(title_text="Volume", row=2, col=1)
            
            return {
                "success": True,
                "chart_type": "candlestick",
                "plotly_json": fig.to_dict(),
                "config": {
                    "displayModeBar": True,
                    "modeBarButtonsToRemove": ["lasso2d", "select2d"]
                }
            }
            
        except Exception as e:
            self.logger.error(f"Candlestick chart generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "title": {
                "type": "string",
                "default": "Candlestick Chart",
                "description": "Chart title"
            },
            "height": {
                "type": "integer",
                "default": 600,
                "description": "Chart height in pixels"
            },
            "show_volume": {
                "type": "boolean",
                "default": False,
                "description": "Show volume subplot"
            },
            "symbol": {
                "type": "string",
                "description": "Filter to specific symbol"
            }
        }


class DistributionChartGenerator(ChartGenerator):
    """Generate distribution charts (histograms, box plots)."""
    
    def __init__(self):
        super().__init__(
            "distribution",
            "Distribution charts for statistical analysis"
        )
    
    def generate(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate distribution chart."""
        try:
            # Configuration
            column = config.get("column", "close")
            chart_type = config.get("chart_type", "histogram")  # histogram, box, violin
            title = config.get("title", f"Distribution of {column}")
            height = config.get("height", 500)
            bins = config.get("bins", 50)
            
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found in dataset")
            
            # Get numeric data
            data = df[column].dropna()
            
            if len(data) == 0:
                raise ValueError(f"No valid data in column '{column}'")
            
            fig = go.Figure()
            
            if chart_type == "histogram":
                fig.add_trace(
                    go.Histogram(
                        x=data,
                        nbinsx=bins,
                        name="Distribution",
                        marker_color="lightblue",
                        opacity=0.7
                    )
                )
                fig.update_layout(
                    xaxis_title=column,
                    yaxis_title="Frequency"
                )
                
            elif chart_type == "box":
                if "symbol" in df.columns:
                    # Box plot by symbol
                    fig = px.box(
                        df, 
                        x="symbol", 
                        y=column,
                        title=title
                    )
                else:
                    fig.add_trace(
                        go.Box(
                            y=data,
                            name=column,
                            marker_color="lightblue"
                        )
                    )
                    fig.update_layout(
                        yaxis_title=column
                    )
                    
            elif chart_type == "violin":
                if "symbol" in df.columns:
                    # Violin plot by symbol
                    fig = px.violin(
                        df,
                        x="symbol",
                        y=column,
                        title=title
                    )
                else:
                    fig.add_trace(
                        go.Violin(
                            y=data,
                            name=column,
                            fillcolor="lightblue",
                            opacity=0.7
                        )
                    )
                    fig.update_layout(
                        yaxis_title=column
                    )
            
            fig.update_layout(
                title=title,
                height=height,
                showlegend=False
            )
            
            return {
                "success": True,
                "chart_type": "distribution",
                "plotly_json": fig.to_dict(),
                "statistics": {
                    "mean": float(data.mean()),
                    "median": float(data.median()),
                    "std": float(data.std()),
                    "min": float(data.min()),
                    "max": float(data.max()),
                    "count": len(data)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Distribution chart generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "column": {
                "type": "string",
                "default": "close",
                "description": "Column to analyze"
            },
            "chart_type": {
                "type": "string",
                "enum": ["histogram", "box", "violin"],
                "default": "histogram",
                "description": "Type of distribution chart"
            },
            "title": {
                "type": "string",
                "description": "Chart title"
            },
            "height": {
                "type": "integer",
                "default": 500,
                "description": "Chart height in pixels"
            },
            "bins": {
                "type": "integer",
                "default": 50,
                "description": "Number of bins for histogram"
            }
        }


class CorrelationChartGenerator(ChartGenerator):
    """Generate correlation heatmaps."""
    
    def __init__(self):
        super().__init__(
            "correlation",
            "Correlation heatmaps for feature analysis"
        )
    
    def generate(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate correlation heatmap."""
        try:
            # Configuration
            columns = config.get("columns", [])
            title = config.get("title", "Correlation Matrix")
            height = config.get("height", 600)
            method = config.get("method", "pearson")  # pearson, spearman, kendall
            
            # Get numeric columns
            numeric_df = df.select_dtypes(include=[np.number])
            
            if columns:
                # Filter to specified columns
                numeric_df = numeric_df[[col for col in columns if col in numeric_df.columns]]
            
            if numeric_df.empty:
                raise ValueError("No numeric columns found for correlation analysis")
            
            # Calculate correlation matrix
            corr_matrix = numeric_df.corr(method=method)
            
            # Create heatmap
            fig = go.Figure(
                data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale="RdBu_r",
                    zmid=0,
                    text=np.round(corr_matrix.values, 3),
                    texttemplate="%{text}",
                    textfont={"size": 10},
                    hovertemplate="<b>%{x} vs %{y}</b><br>" +
                                "Correlation: %{z:.3f}<br>" +
                                "<extra></extra>"
                )
            )
            
            fig.update_layout(
                title=title,
                height=height,
                xaxis_title="Features",
                yaxis_title="Features"
            )
            
            return {
                "success": True,
                "chart_type": "correlation",
                "plotly_json": fig.to_dict(),
                "correlation_matrix": corr_matrix.to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"Correlation chart generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Columns to include in correlation (default: all numeric)"
            },
            "title": {
                "type": "string",
                "default": "Correlation Matrix",
                "description": "Chart title"
            },
            "height": {
                "type": "integer",
                "default": 600,
                "description": "Chart height in pixels"
            },
            "method": {
                "type": "string",
                "enum": ["pearson", "spearman", "kendall"],
                "default": "pearson",
                "description": "Correlation method"
            }
        }


class ScatterChartGenerator(ChartGenerator):
    """Generate scatter plots for relationship analysis."""
    
    def __init__(self):
        super().__init__(
            "scatter",
            "Scatter plots for analyzing relationships between variables"
        )
    
    def generate(self, df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scatter plot."""
        try:
            # Configuration
            x_column = config.get("x_column", "volume")
            y_column = config.get("y_column", "close")
            color_column = config.get("color_column")
            size_column = config.get("size_column")
            title = config.get("title", f"{y_column} vs {x_column}")
            height = config.get("height", 500)
            
            # Validate columns
            required_cols = [x_column, y_column]
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Create scatter plot
            scatter_kwargs = {
                "x": df[x_column],
                "y": df[y_column],
                "title": title,
                "height": height
            }
            
            if color_column and color_column in df.columns:
                scatter_kwargs["color"] = df[color_column]
            
            if size_column and size_column in df.columns:
                scatter_kwargs["size"] = df[size_column]
            
            fig = px.scatter(df, **scatter_kwargs)
            
            # Add trendline if requested
            if config.get("show_trendline", False):
                # Calculate trendline
                x_vals = df[x_column].dropna()
                y_vals = df[y_column].dropna()
                
                if len(x_vals) > 1 and len(y_vals) > 1:
                    z = np.polyfit(x_vals, y_vals, 1)
                    p = np.poly1d(z)
                    
                    fig.add_trace(
                        go.Scatter(
                            x=x_vals,
                            y=p(x_vals),
                            mode="lines",
                            name="Trendline",
                            line=dict(color="red", dash="dash")
                        )
                    )
            
            fig.update_layout(
                xaxis_title=x_column,
                yaxis_title=y_column
            )
            
            # Calculate correlation
            correlation = df[x_column].corr(df[y_column])
            
            return {
                "success": True,
                "chart_type": "scatter",
                "plotly_json": fig.to_dict(),
                "correlation": float(correlation) if not np.isnan(correlation) else None
            }
            
        except Exception as e:
            self.logger.error(f"Scatter chart generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema."""
        return {
            "x_column": {
                "type": "string",
                "default": "volume",
                "description": "Column for X-axis"
            },
            "y_column": {
                "type": "string", 
                "default": "close",
                "description": "Column for Y-axis"
            },
            "color_column": {
                "type": "string",
                "description": "Column to use for color coding"
            },
            "size_column": {
                "type": "string",
                "description": "Column to use for point sizing"
            },
            "title": {
                "type": "string",
                "description": "Chart title"
            },
            "height": {
                "type": "integer",
                "default": 500,
                "description": "Chart height in pixels"
            },
            "show_trendline": {
                "type": "boolean",
                "default": False,
                "description": "Show linear trendline"
            }
        }


class DataVisualizationService:
    """Main service for creating data visualizations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.settings = get_settings()
        
        # Initialize chart generators
        self.generators = {
            "time_series": TimeSeriesChartGenerator(),
            "candlestick": CandlestickChartGenerator(),
            "distribution": DistributionChartGenerator(),
            "correlation": CorrelationChartGenerator(),
            "scatter": ScatterChartGenerator()
        }
    
    async def create_chart(self, dataset_id: str, chart_config: Dict[str, Any], 
                          user_id: str, db: AsyncSession) -> Dict[str, Any]:
        """Create a chart from dataset."""
        try:
            # Get dataset
            result = await db.execute(
                select(Dataset).where(
                    Dataset.id == UUID(dataset_id),
                    Dataset.user_id == UUID(user_id)
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {"success": False, "error": "Dataset not found"}
            
            # Load dataset
            df = await self._load_dataset(dataset)
            if df is None:
                return {"success": False, "error": "Failed to load dataset"}
            
            # Get chart type and configuration
            chart_type = chart_config.get("chart_type", "time_series")
            
            if chart_type not in self.generators:
                return {
                    "success": False,
                    "error": f"Unsupported chart type: {chart_type}"
                }
            
            # Apply data sampling if dataset is large
            sample_size = chart_config.get("sample_size", 10000)
            if len(df) > sample_size:
                df = df.sample(n=sample_size).sort_index()
                self.logger.info(f"Sampled {sample_size} rows from {len(df)} total rows")
            
            # Generate chart
            generator = self.generators[chart_type]
            chart_result = generator.generate(df, chart_config)
            
            if chart_result.get("success"):
                # Add metadata
                chart_result.update({
                    "dataset_id": dataset_id,
                    "dataset_name": dataset.name,
                    "rows_used": len(df),
                    "generated_at": datetime.utcnow().isoformat()
                })
            
            return chart_result
            
        except Exception as e:
            self.logger.error(f"Chart creation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_dataset_preview(self, dataset_id: str, user_id: str, 
                                   db: AsyncSession) -> Dict[str, Any]:
        """Create a comprehensive preview with multiple charts."""
        try:
            # Get dataset
            result = await db.execute(
                select(Dataset).where(
                    Dataset.id == UUID(dataset_id),
                    Dataset.user_id == UUID(user_id)
                )
            )
            dataset = result.scalar_one_or_none()
            
            if not dataset:
                return {"success": False, "error": "Dataset not found"}
            
            # Load dataset (sample for preview)
            df = await self._load_dataset(dataset, sample_size=5000)
            if df is None:
                return {"success": False, "error": "Failed to load dataset"}
            
            preview_data = {
                "dataset_info": {
                    "id": dataset_id,
                    "name": dataset.name,
                    "asset_class": dataset.asset_class.value,
                    "total_rows": dataset.row_count,
                    "preview_rows": len(df),
                    "columns": df.columns.tolist()
                },
                "sample_data": df.head(20).to_dict("records"),
                "charts": {}
            }
            
            # Generate appropriate charts based on asset class and available columns
            charts_to_generate = self._get_default_charts(df, dataset.asset_class)
            
            for chart_name, chart_config in charts_to_generate.items():
                try:
                    generator = self.generators[chart_config["chart_type"]]
                    chart_result = generator.generate(df, chart_config)
                    
                    if chart_result.get("success"):
                        preview_data["charts"][chart_name] = chart_result
                    
                except Exception as e:
                    self.logger.warning(f"Failed to generate {chart_name} chart: {str(e)}")
            
            # Add basic statistics
            preview_data["statistics"] = self._calculate_basic_stats(df)
            
            return {
                "success": True,
                "preview": preview_data
            }
            
        except Exception as e:
            self.logger.error(f"Dataset preview creation failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _load_dataset(self, dataset: Dataset, sample_size: Optional[int] = None) -> Optional[pd.DataFrame]:
        """Load dataset from storage."""
        try:
            if not dataset.file_path or not os.path.exists(dataset.file_path):
                self.logger.error(f"Dataset file not found: {dataset.file_path}")
                return None
            
            # Load based on format
            if dataset.data_format.value == "parquet":
                df = pd.read_parquet(dataset.file_path)
            elif dataset.data_format.value == "csv":
                df = pd.read_csv(dataset.file_path)
            elif dataset.data_format.value == "json":
                df = pd.read_json(dataset.file_path)
            else:
                self.logger.error(f"Unsupported data format: {dataset.data_format}")
                return None
            
            # Apply sampling if requested
            if sample_size and len(df) > sample_size:
                df = df.sample(n=sample_size).sort_index()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to load dataset: {str(e)}")
            return None
    
    def _get_default_charts(self, df: pd.DataFrame, asset_class: AssetClass) -> Dict[str, Dict[str, Any]]:
        """Get default charts to generate based on data characteristics."""
        charts = {}
        
        # Time series chart if timestamp column exists
        if "timestamp" in df.columns:
            if all(col in df.columns for col in ["open", "high", "low", "close"]):
                # OHLC data - use candlestick
                charts["price_chart"] = {
                    "chart_type": "candlestick",
                    "title": f"{asset_class.value.title()} Price Chart",
                    "show_volume": "volume" in df.columns
                }
            elif "close" in df.columns:
                # Just close price - use time series
                charts["price_chart"] = {
                    "chart_type": "time_series",
                    "y_columns": ["close"],
                    "title": f"{asset_class.value.title()} Price Chart",
                    "show_volume": "volume" in df.columns
                }
        
        # Distribution chart for price data
        if "close" in df.columns:
            charts["price_distribution"] = {
                "chart_type": "distribution",
                "column": "close",
                "chart_type": "histogram",
                "title": "Price Distribution"
            }
        
        # Volume distribution if available
        if "volume" in df.columns:
            charts["volume_distribution"] = {
                "chart_type": "distribution",
                "column": "volume",
                "chart_type": "histogram",
                "title": "Volume Distribution"
            }
        
        # Correlation heatmap if multiple numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 2:
            charts["correlation_matrix"] = {
                "chart_type": "correlation",
                "columns": numeric_cols[:10],  # Limit to first 10 numeric columns
                "title": "Feature Correlation Matrix"
            }
        
        # Scatter plot for price vs volume
        if "close" in df.columns and "volume" in df.columns:
            charts["price_volume_scatter"] = {
                "chart_type": "scatter",
                "x_column": "volume",
                "y_column": "close",
                "title": "Price vs Volume",
                "show_trendline": True
            }
        
        return charts
    
    def _calculate_basic_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate basic statistics for the dataset."""
        try:
            numeric_df = df.select_dtypes(include=[np.number])
            
            stats = {
                "shape": df.shape,
                "missing_values": df.isnull().sum().to_dict(),
                "data_types": df.dtypes.astype(str).to_dict()
            }
            
            if not numeric_df.empty:
                stats["numeric_summary"] = numeric_df.describe().to_dict()
            
            # Date range if timestamp column exists
            if "timestamp" in df.columns:
                try:
                    timestamps = pd.to_datetime(df["timestamp"])
                    stats["date_range"] = {
                        "start": timestamps.min().isoformat(),
                        "end": timestamps.max().isoformat(),
                        "span_days": (timestamps.max() - timestamps.min()).days
                    }
                except:
                    pass
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to calculate basic stats: {str(e)}")
            return {}
    
    def get_available_chart_types(self) -> Dict[str, Any]:
        """Get information about available chart types."""
        chart_types = {}
        
        for chart_type, generator in self.generators.items():
            chart_types[chart_type] = {
                "name": generator.chart_type,
                "description": generator.description,
                "config_schema": generator.get_config_schema()
            }
        
        return chart_types