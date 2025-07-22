'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/no-code/card';
import { Button } from '@/components/ui/no-code/button';
import { Badge } from '@/components/ui/no-code/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/no-code/tabs';
import { Input } from '@/components/ui/no-code/input';
import { Label } from '@/components/ui/no-code/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/no-code/select';
import { 
  Database, 
  Upload, 
  Search, 
  Filter, 
  Calendar,
  BarChart3,
  TrendingUp,
  DollarSign
} from 'lucide-react';

interface DatasetSelectorProps {
  onNext: () => void;
}

const platformDatasets = [
  {
    id: 'crypto-1h-2020-2024',
    name: 'Cryptocurrency 1H (2020-2024)',
    description: 'Hourly cryptocurrency data for major coins',
    size: '2.5M records',
    symbols: ['BTC', 'ETH', 'ADA', 'DOT', 'SOL'],
    timeframe: '1H',
    dateRange: '2020-01-01 to 2024-01-01',
    type: 'platform'
  },
  {
    id: 'stocks-daily-sp500',
    name: 'S&P 500 Daily (2015-2024)',
    description: 'Daily stock data for S&P 500 companies',
    size: '1.8M records',
    symbols: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
    timeframe: 'Daily',
    dateRange: '2015-01-01 to 2024-01-01',
    type: 'platform'
  },
  {
    id: 'forex-1h-majors',
    name: 'Forex Major Pairs 1H (2018-2024)',
    description: 'Hourly forex data for major currency pairs',
    size: '3.2M records',
    symbols: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'],
    timeframe: '1H',
    dateRange: '2018-01-01 to 2024-01-01',
    type: 'platform'
  }
];

const userDatasets = [
  {
    id: 'user-custom-crypto',
    name: 'My Custom Crypto Dataset',
    description: 'Custom uploaded cryptocurrency data',
    size: '500K records',
    symbols: ['BTC', 'ETH'],
    timeframe: '5M',
    dateRange: '2023-01-01 to 2023-12-31',
    type: 'user'
  }
];

export function DatasetSelector({ onNext }: DatasetSelectorProps) {
  const [selectedDataset, setSelectedDataset] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');

  const handleDatasetSelect = (datasetId: string) => {
    setSelectedDataset(datasetId);
  };

  const handleNext = () => {
    if (selectedDataset) {
      onNext();
    }
  };

  const renderDatasetCard = (dataset: any) => (
    <Card 
      key={dataset.id}
      className={`cursor-pointer transition-all ${
        selectedDataset === dataset.id 
          ? 'ring-2 ring-blue-500 bg-blue-50' 
          : 'hover:shadow-md'
      }`}
      onClick={() => handleDatasetSelect(dataset.id)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base">{dataset.name}</CardTitle>
            <CardDescription className="text-sm mt-1">
              {dataset.description}
            </CardDescription>
          </div>
          <Badge variant={dataset.type === 'platform' ? 'default' : 'secondary'}>
            {dataset.type}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
            <span>{dataset.size}</span>
          </div>
          <div className="flex items-center space-x-2">
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
            <span>{dataset.timeframe}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Calendar className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs">{dataset.dateRange}</span>
          </div>
          <div className="flex items-center space-x-2">
            <DollarSign className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs">{dataset.symbols.slice(0, 3).join(', ')}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">Select Training Dataset</h2>
        <p className="text-muted-foreground">
          Choose a dataset to train your model on, or upload your own data
        </p>
      </div>

      {/* Search and Filter */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search datasets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Select value={filterType} onValueChange={setFilterType}>
          <SelectTrigger className="w-48">
            <Filter className="h-4 w-4 mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="crypto">Cryptocurrency</SelectItem>
            <SelectItem value="stocks">Stocks</SelectItem>
            <SelectItem value="forex">Forex</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Tabs defaultValue="platform" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="platform">
            <Database className="h-4 w-4 mr-2" />
            Platform Datasets
          </TabsTrigger>
          <TabsTrigger value="user">
            <Upload className="h-4 w-4 mr-2" />
            My Datasets
          </TabsTrigger>
          <TabsTrigger value="upload">
            <Upload className="h-4 w-4 mr-2" />
            Upload New
          </TabsTrigger>
        </TabsList>

        <TabsContent value="platform" className="space-y-4">
          <div className="grid gap-4">
            {platformDatasets.map(renderDatasetCard)}
          </div>
        </TabsContent>

        <TabsContent value="user" className="space-y-4">
          <div className="grid gap-4">
            {userDatasets.map(renderDatasetCard)}
            {userDatasets.length === 0 && (
              <Card>
                <CardContent className="p-8 text-center">
                  <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium mb-2">No Custom Datasets</h3>
                  <p className="text-muted-foreground mb-4">
                    You haven't uploaded any datasets yet. Upload your first dataset to get started.
                  </p>
                  <Button variant="outline">Upload Dataset</Button>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="upload" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upload Custom Dataset</CardTitle>
              <CardDescription>
                Upload your own CSV file with trading data. Make sure it includes OHLCV columns.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="dataset-name">Dataset Name</Label>
                <Input id="dataset-name" placeholder="My Custom Dataset" />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="dataset-description">Description</Label>
                <Input id="dataset-description" placeholder="Description of your dataset" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="timeframe">Timeframe</Label>
                  <Select>
                    <SelectTrigger>
                      <SelectValue placeholder="Select timeframe" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1m">1 Minute</SelectItem>
                      <SelectItem value="5m">5 Minutes</SelectItem>
                      <SelectItem value="1h">1 Hour</SelectItem>
                      <SelectItem value="1d">1 Day</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="symbols">Symbols</Label>
                  <Input id="symbols" placeholder="BTC, ETH, ADA" />
                </div>
              </div>

              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">Drop your CSV file here</h3>
                <p className="text-muted-foreground mb-4">
                  Or click to browse and select a file
                </p>
                <Button variant="outline">Choose File</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Action Buttons */}
      <div className="flex justify-between">
        <Button variant="outline">
          Back to Design
        </Button>
        <Button 
          onClick={handleNext}
          disabled={!selectedDataset}
          className="bg-blue-600 hover:bg-blue-700"
        >
          Start Training
        </Button>
      </div>
    </div>
  );
}