'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { X, Plus, Upload, AlertTriangle, Bug, HelpCircle, Settings, CreditCard } from 'lucide-react';
import { 
  customerSupportApi, 
  CreateTicketRequest,
  TicketCategory, 
  TicketPriority,
  formatCategory,
  formatPriority
} from '@/lib/api/customer-support-api';
import { toast } from 'react-hot-toast';

interface CreateTicketModalProps {
  isOpen: boolean;
  onClose: () => void;
  onTicketCreated: () => void;
  userId: string;
  userEmail?: string;
}

const CATEGORY_ICONS = {
  [TicketCategory.TECHNICAL]: Bug,
  [TicketCategory.BUG_REPORT]: Bug,
  [TicketCategory.STRATEGY_DEVELOPMENT]: Settings,
  [TicketCategory.LIVE_TRADING]: AlertTriangle,
  [TicketCategory.PAPER_TRADING]: Settings,
  [TicketCategory.BROKER_INTEGRATION]: Settings,
  [TicketCategory.MODEL_TRAINING]: Settings,
  [TicketCategory.BACKTESTING]: Settings,
  [TicketCategory.ACCOUNT_BILLING]: CreditCard,
  [TicketCategory.KYC_VERIFICATION]: Settings,
  [TicketCategory.API_SDK]: Settings,
  [TicketCategory.MARKETPLACE]: Settings,
  [TicketCategory.SECURITY]: AlertTriangle,
  [TicketCategory.DATA_PRIVACY]: Settings,
  [TicketCategory.FEATURE_REQUEST]: Plus,
  [TicketCategory.GENERAL_INQUIRY]: HelpCircle,
  [TicketCategory.OTHER]: HelpCircle,
};

export default function CreateTicketModal({ 
  isOpen, 
  onClose, 
  onTicketCreated, 
  userId, 
  userEmail 
}: CreateTicketModalProps) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: '' as TicketCategory | '',
    priority: '' as TicketPriority | '',
    userPhone: '',
    preferredContactMethod: 'EMAIL',
    browserInfo: '',
    operatingSystem: '',
    platformVersion: '',
    errorLogs: ''
  });
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [attachments, setAttachments] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.title.trim() || !formData.description.trim() || !formData.category) {
      toast.error('Please fill in all required fields');
      return;
    }

    setIsSubmitting(true);

    try {
      const request: CreateTicketRequest = {
        userId,
        title: formData.title.trim(),
        description: formData.description.trim(),
        category: formData.category,
        priority: formData.priority || undefined,
        tags: tags.length > 0 ? tags : undefined,
        userEmail: userEmail || undefined,
        userPhone: formData.userPhone || undefined,
        preferredContactMethod: formData.preferredContactMethod || undefined,
        browserInfo: formData.browserInfo || undefined,
        operatingSystem: formData.operatingSystem || undefined,
        platformVersion: formData.platformVersion || undefined,
        errorLogs: formData.errorLogs || undefined,
        attachments: attachments.length > 0 ? attachments : undefined
      };

      await customerSupportApi.createTicket(request);
      
      toast.success('Support ticket created successfully');
      onTicketCreated();
      onClose();
      resetForm();
    } catch (error) {
      console.error('Failed to create ticket:', error);
      toast.error('Failed to create ticket. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      category: '' as TicketCategory | '',
      priority: '' as TicketPriority | '',
      userPhone: '',
      preferredContactMethod: 'EMAIL',
      browserInfo: '',
      operatingSystem: '',
      platformVersion: '',
      errorLogs: ''
    });
    setTags([]);
    setTagInput('');
    setAttachments([]);
  };

  const addTag = () => {
    const trimmedTag = tagInput.trim();
    if (trimmedTag && !tags.includes(trimmedTag)) {
      setTags([...tags, trimmedTag]);
      setTagInput('');
    }
  };

  const removeTag = (tagToRemove: string) => {
    setTags(tags.filter(tag => tag !== tagToRemove));
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag();
    }
  };

  const getCategoryIcon = (category: TicketCategory) => {
    const IconComponent = CATEGORY_ICONS[category] || HelpCircle;
    return <IconComponent className="w-4 h-4" />;
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <HelpCircle className="w-5 h-5" />
            Create Support Ticket
          </DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="title" className="text-sm font-medium">
                Title <span className="text-red-500">*</span>
              </Label>
              <Input
                id="title"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                placeholder="Brief description of your issue"
                className="mt-1"
                required
              />
            </div>

            <div>
              <Label htmlFor="description" className="text-sm font-medium">
                Description <span className="text-red-500">*</span>
              </Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                placeholder="Please provide detailed information about your issue"
                rows={4}
                className="mt-1"
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="category" className="text-sm font-medium">
                  Category <span className="text-red-500">*</span>
                </Label>
                <Select
                  value={formData.category}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, category: value as TicketCategory }))}
                  required
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(TicketCategory).map(category => (
                      <SelectItem key={category} value={category}>
                        <div className="flex items-center gap-2">
                          {getCategoryIcon(category)}
                          {formatCategory(category)}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="priority" className="text-sm font-medium">
                  Priority (optional)
                </Label>
                <Select
                  value={formData.priority}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, priority: value as TicketPriority }))}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue placeholder="Auto-determined" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.values(TicketPriority).map(priority => (
                      <SelectItem key={priority} value={priority}>
                        {formatPriority(priority)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Tags */}
          <div>
            <Label className="text-sm font-medium">Tags</Label>
            <div className="flex flex-wrap gap-2 mb-2">
              {tags.map(tag => (
                <Badge key={tag} variant="secondary" className="flex items-center gap-1">
                  {tag}
                  <button
                    type="button"
                    onClick={() => removeTag(tag)}
                    className="hover:text-red-500"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
            </div>
            <div className="flex gap-2">
              <Input
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Add tags to help categorize your issue"
                className="flex-1"
              />
              <Button type="button" onClick={addTag} variant="outline" size="sm">
                <Plus className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Contact Information */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-900">Contact Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="userPhone" className="text-sm font-medium">
                  Phone Number
                </Label>
                <Input
                  id="userPhone"
                  value={formData.userPhone}
                  onChange={(e) => setFormData(prev => ({ ...prev, userPhone: e.target.value }))}
                  placeholder="Optional phone number"
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="preferredContact" className="text-sm font-medium">
                  Preferred Contact Method
                </Label>
                <Select
                  value={formData.preferredContactMethod}
                  onValueChange={(value) => setFormData(prev => ({ ...prev, preferredContactMethod: value }))}
                >
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="EMAIL">Email</SelectItem>
                    <SelectItem value="PHONE">Phone</SelectItem>
                    <SelectItem value="CHAT">Live Chat</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Technical Information */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-900">Technical Information (optional)</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="browserInfo" className="text-sm font-medium">
                  Browser Information
                </Label>
                <Input
                  id="browserInfo"
                  value={formData.browserInfo}
                  onChange={(e) => setFormData(prev => ({ ...prev, browserInfo: e.target.value }))}
                  placeholder="e.g., Chrome 120.0.6099.224"
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="operatingSystem" className="text-sm font-medium">
                  Operating System
                </Label>
                <Input
                  id="operatingSystem"
                  value={formData.operatingSystem}
                  onChange={(e) => setFormData(prev => ({ ...prev, operatingSystem: e.target.value }))}
                  placeholder="e.g., Windows 11, macOS 14.1"
                  className="mt-1"
                />
              </div>
            </div>

            <div>
              <Label htmlFor="platformVersion" className="text-sm font-medium">
                Platform Version
              </Label>
              <Input
                id="platformVersion"
                value={formData.platformVersion}
                onChange={(e) => setFormData(prev => ({ ...prev, platformVersion: e.target.value }))}
                placeholder="e.g., v2.1.0"
                className="mt-1"
              />
            </div>

            <div>
              <Label htmlFor="errorLogs" className="text-sm font-medium">
                Error Logs or Messages
              </Label>
              <Textarea
                id="errorLogs"
                value={formData.errorLogs}
                onChange={(e) => setFormData(prev => ({ ...prev, errorLogs: e.target.value }))}
                placeholder="Copy and paste any error messages or logs"
                rows={3}
                className="mt-1"
              />
            </div>
          </div>

          {/* File Attachments */}
          <div>
            <Label className="text-sm font-medium">Attachments</Label>
            <div className="mt-1 border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
              <Upload className="w-8 h-8 mx-auto text-gray-400" />
              <p className="mt-2 text-sm text-gray-600">
                Drag and drop files here, or click to select
              </p>
              <p className="text-xs text-gray-500">
                Supported formats: PNG, JPG, PDF, TXT (max 10MB)
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Ticket'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}