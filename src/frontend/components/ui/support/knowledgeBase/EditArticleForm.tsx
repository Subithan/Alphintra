'use client';

import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { DialogClose, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { X } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/index';
import { articleSchema } from '@/lib/api/schemas';

interface EditArticleFormProps {
  article: {
    id: string;
    title: string;
    category: string;
    status: string;
    author: string;
    updated: string;
    views: number;
    excerpt: string;
    tags: string[];
  };
  onEditArticle: (data: {
    id: string;
    title: string;
    category: string;
    status: string;
    author: string;
    updated: string;
    views: number;
    excerpt: string;
    tags: string[];
  }) => void;
}

export default function EditArticleForm({ article, onEditArticle }: EditArticleFormProps) {
  const [open, setOpen] = useState(true);
  const [formData, setFormData] = useState({
    title: article.title,
    category: article.category,
    status: article.status,
    author: article.author,
    excerpt: article.excerpt,
    tags: article.tags,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof typeof formData, string>>>({});
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  const validateForm = (): boolean => {
    const result = articleSchema.safeParse(formData);
    if (!result.success) {
      const newErrors = result.error.flatten().fieldErrors;
      setErrors({
        title: newErrors.title?.[0],
        category: newErrors.category?.[0],
        status: newErrors.status?.[0],
        author: newErrors.author?.[0],
        excerpt: newErrors.excerpt?.[0],
        tags: newErrors.tags?.[0],
      });
      return false;
    }
    setErrors({});
    return true;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    onEditArticle({
      ...formData,
      id: article.id,
      updated: new Date().toLocaleDateString('en-US', {
        month: 'short',
        day: '2-digit',
        year: 'numeric',
      }) + ' ' + new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      views: article.views,
    });

    setOpen(false);
    if (closeButtonRef.current) {
      closeButtonRef.current.click();
    }
  };

  const handleTagChange = (index: number, value: string) => {
    const newTags = [...formData.tags];
    newTags[index] = value;
    setFormData({ ...formData, tags: newTags });
  };

  const addTagField = () => {
    setFormData({ ...formData, tags: [...formData.tags, ''] });
  };

  return (
    <DialogContent className="max-w-2xl">
      <DialogHeader>
        <DialogTitle className="text-black dark:text-white">Edit Article: {article.title}</DialogTitle>
      </DialogHeader>
      <DialogClose
        ref={closeButtonRef}
        className="absolute right-4 top-4 rounded-md p-1 transition-colors hover:bg-muted focus:outline-none focus:ring-2 focus:ring-ring"
      >
        <X className="h-4 w-4 text-black dark:text-white" />
        <span className="sr-only">Close</span>
      </DialogClose>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            className="mt-1"
          />
          {errors.title && <p className="text-sm text-red-500 mt-1">{errors.title}</p>}
        </div>
        <div>
          <Label htmlFor="category">Category</Label>
          <Select
            value={formData.category}
            onValueChange={(value) => setFormData({ ...formData, category: value })}
          >
            <SelectTrigger id="category" className="mt-1">
              <SelectValue placeholder="Select category" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Account Management">Account Management</SelectItem>
              <SelectItem value="Billing">Billing</SelectItem>
              <SelectItem value="Features">Features</SelectItem>
              <SelectItem value="Troubleshooting">Troubleshooting</SelectItem>
              <SelectItem value="API Documentation">API Documentation</SelectItem>
            </SelectContent>
          </Select>
          {errors.category && <p className="text-sm text-red-500 mt-1">{errors.category}</p>}
        </div>
        <div>
          <Label htmlFor="status">Status</Label>
          <Select
            value={formData.status}
            onValueChange={(value) => setFormData({ ...formData, status: value })}
          >
            <SelectTrigger id="status" className="mt-1">
              <SelectValue placeholder="Select status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="published">Published</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>
          {errors.status && <p className="text-sm text-red-500 mt-1">{errors.status}</p>}
        </div>
        <div>
          <Label htmlFor="author">Author</Label>
          <Input
            id="author"
            value={formData.author}
            onChange={(e) => setFormData({ ...formData, author: e.target.value })}
            className="mt-1"
          />
          {errors.author && <p className="text-sm text-red-500 mt-1">{errors.author}</p>}
        </div>
        <div>
          <Label htmlFor="excerpt">Excerpt</Label>
          <Textarea
            id="excerpt"
            value={formData.excerpt}
            onChange={(e) => setFormData({ ...formData, excerpt: e.target.value })}
            className="mt-1"
          />
          {errors.excerpt && <p className="text-sm text-red-500 mt-1">{errors.excerpt}</p>}
        </div>
        <div>
          <Label>Tags</Label>
          {formData.tags.map((tag, index) => (
            <div key={index} className="flex items-center gap-2 mt-1">
              <Input
                value={tag}
                onChange={(e) => handleTagChange(index, e.target.value)}
                placeholder={`Tag ${index + 1}`}
              />
            </div>
          ))}
          {errors.tags && <p className="text-sm text-red-500 mt-1">{errors.tags}</p>}
          <Button
            type="button"
            variant="outline"
            className="mt-2"
            onClick={addTagField}
          >
            Add Tag
          </Button>
        </div>
        <Button type="submit" className="bg-yellow-500 hover:bg-yellow-500 hover:scale-105 mt-4">
          Save Changes
        </Button>
      </form>
    </DialogContent>
  );
}