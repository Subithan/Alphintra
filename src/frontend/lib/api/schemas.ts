import { z } from 'zod';

export const ticketSchema = z.object({
  priority: z.enum(['low', 'medium', 'high', 'urgent'], { message: 'Invalid priority' }),
  status: z.enum(['open', 'in-progress', 'pending', 'resolved'], { message: 'Invalid status' }),
});

export const articleSchema = z.object({
  title: z.string().min(5, 'Title must be at least 5 characters'),
  category: z.enum(['Account Management', 'Billing', 'Features', 'Troubleshooting', 'API Documentation'], {
    message: 'Invalid category',
  }),
  status: z.enum(['published', 'draft', 'archived'], { message: 'Invalid status' }),
  author: z.string().min(2, 'Author must be at least 2 characters'),
  excerpt: z.string().min(10, 'Excerpt must be at least 10 characters'),
  tags: z.array(z.string().min(1, 'Tags cannot be empty')).min(1, 'At least one tag is required'),
});

export const escalationRuleSchema = z.object({
  name: z.string().min(3, 'Rule name must be at least 3 characters'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  trigger: z.enum(['Response Time', 'Priority Level', 'Customer Tier', 'Reopen Count'], {
    message: 'Invalid trigger type',
  }),
  condition: z.string().min(3, 'Condition must be at least 3 characters'),
  action: z.enum(['Assign to Manager', 'Notify Director', 'Senior Support Review', 'External Escalation'], {
    message: 'Invalid action',
  }),
  status: z.enum(['active', 'inactive'], { message: 'Invalid status' }),
});