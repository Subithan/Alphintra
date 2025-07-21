import { NodeConfigFields, NodeConfigResult } from './types';
import { commonFields, assetClassOptions } from './commonFields';

export function getDataSourceConfig(): NodeConfigResult {
  const fields: NodeConfigFields = {
    assetClass: {
      type: 'select',
      label: 'Asset Class',
      description: 'Type of financial instrument',
      options: assetClassOptions,
      default: 'stocks'
    },

    symbol: commonFields.symbol,
    timeframe: commonFields.timeframe,

    dataSource: {
      type: 'select',
      label: 'Data Source',
      description: 'Choose between system datasets or user upload',
      options: [
        { value: 'system', label: 'System Dataset' },
      ],
      default: 'system'
    },

    bars: {
      type: 'number',
      label: 'Number of Bars',
      description: 'How many historical bars to fetch',
      min: 100,
      max: 50000,
      default: 1000
    },

    startDate: {
      type: 'text',
      label: 'Start Date (Optional)',
      description: 'Start date for historical data (YYYY-MM-DD)',
      placeholder: '2023-01-01'
    },

    endDate: {
      type: 'text',
      label: 'End Date (Optional)',
      description: 'End date for historical data (YYYY-MM-DD)',
      placeholder: '2024-01-01'
    }
  };

  const shouldShowField = (key: string, config: any, params: Record<string, any>) => {
    switch (key) {
      case 'startDate':
      case 'endDate':
      case 'bars':
        return params.dataSource === 'system';
      
      default:
        return true;
    }
  };

  return { fields, shouldShowField };
}

export function getCustomDatasetConfig(): NodeConfigResult {
  const fields: NodeConfigFields = {
    fileName: {
      type: 'text',
      label: 'File Name',
      description: 'Name of the uploaded file',
      placeholder: 'my_dataset.csv',
      default: 'No file uploaded'
    },

    fileUpload: {
      type: 'text',
      label: 'Upload Dataset',
      description: 'Upload CSV or Excel file with OHLCV data',
      placeholder: 'Click to upload file...'
    },

    dateColumn: {
      type: 'select',
      label: 'Date Column',
      description: 'Column containing date/timestamp',
      options: [
        { value: 'Date', label: 'Date' },
        { value: 'Timestamp', label: 'Timestamp' },
        { value: 'DateTime', label: 'DateTime' },
        { value: 'Time', label: 'Time' },
      ],
      default: 'Date'
    },

    openColumn: {
      type: 'select',
      label: 'Open Price Column',
      description: 'Column containing opening prices',
      options: [
        { value: 'Open', label: 'Open' },
        { value: 'open', label: 'open' },
        { value: 'OPEN', label: 'OPEN' },
        { value: 'O', label: 'O' },
      ],
      default: 'Open'
    },

    highColumn: {
      type: 'select',
      label: 'High Price Column',
      description: 'Column containing high prices',
      options: [
        { value: 'High', label: 'High' },
        { value: 'high', label: 'high' },
        { value: 'HIGH', label: 'HIGH' },
        { value: 'H', label: 'H' },
      ],
      default: 'High'
    },

    lowColumn: {
      type: 'select',
      label: 'Low Price Column',
      description: 'Column containing low prices',
      options: [
        { value: 'Low', label: 'Low' },
        { value: 'low', label: 'low' },
        { value: 'LOW', label: 'LOW' },
        { value: 'L', label: 'L' },
      ],
      default: 'Low'
    },

    closeColumn: {
      type: 'select',
      label: 'Close Price Column',
      description: 'Column containing closing prices',
      options: [
        { value: 'Close', label: 'Close' },
        { value: 'close', label: 'close' },
        { value: 'CLOSE', label: 'CLOSE' },
        { value: 'C', label: 'C' },
      ],
      default: 'Close'
    },

    volumeColumn: {
      type: 'select',
      label: 'Volume Column (Optional)',
      description: 'Column containing volume data',
      options: [
        { value: 'Volume', label: 'Volume' },
        { value: 'volume', label: 'volume' },
        { value: 'VOLUME', label: 'VOLUME' },
        { value: 'Vol', label: 'Vol' },
        { value: 'V', label: 'V' },
      ],
      default: 'Volume'
    },

    normalization: {
      type: 'select',
      label: 'Data Normalization',
      description: 'How to normalize the data',
      options: [
        { value: 'none', label: 'No Normalization' },
        { value: 'minmax', label: 'Min-Max Scaling' },
        { value: 'zscore', label: 'Z-Score Normalization' },
        { value: 'percentage', label: 'Percentage Change' },
      ],
      default: 'none'
    },

    missingValues: {
      type: 'select',
      label: 'Missing Value Handling',
      description: 'How to handle missing values',
      options: [
        { value: 'drop', label: 'Drop Missing Rows' },
        { value: 'forward_fill', label: 'Forward Fill' },
        { value: 'backward_fill', label: 'Backward Fill' },
        { value: 'interpolate', label: 'Linear Interpolation' },
        { value: 'zero', label: 'Fill with Zero' },
      ],
      default: 'forward_fill'
    },

    validateData: {
      type: 'boolean',
      label: 'Validate Data Quality',
      description: 'Run data quality checks on upload',
      default: true
    }
  };

  return { fields };
}

export function validateDataSourceConfig(params: Record<string, any>): string[] {
  const errors: string[] = [];

  if (params.bars && (params.bars < 100 || params.bars > 50000)) {
    errors.push('Number of bars must be between 100 and 50,000');
  }

  // Validate date format if provided
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (params.startDate && !dateRegex.test(params.startDate)) {
    errors.push('Start date must be in YYYY-MM-DD format');
  }

  if (params.endDate && !dateRegex.test(params.endDate)) {
    errors.push('End date must be in YYYY-MM-DD format');
  }

  if (params.startDate && params.endDate && new Date(params.startDate) >= new Date(params.endDate)) {
    errors.push('Start date must be before end date');
  }

  return errors;
}

export function validateCustomDatasetConfig(params: Record<string, any>): string[] {
  const errors: string[] = [];

  if (!params.fileName || params.fileName === 'No file uploaded') {
    errors.push('Please upload a dataset file');
  }

  // Check for duplicate column mappings
  const columns = [params.dateColumn, params.openColumn, params.highColumn, params.lowColumn, params.closeColumn];
  const uniqueColumns = new Set(columns.filter(Boolean));
  
  if (uniqueColumns.size !== columns.filter(Boolean).length) {
    errors.push('Each column can only be mapped once');
  }

  return errors;
}