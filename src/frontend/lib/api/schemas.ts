import { z } from 'zod';

export const userSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  phone: z.string().regex(/^\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}$/, 'Invalid phone number'),
  location: z.string().min(2, 'Location must be at least 2 characters'),
  tier: z.enum(['premium', 'standard', 'basic'], { message: 'Invalid account tier' }),
  status: z.enum(['active', 'pending', 'inactive'], { message: 'Invalid status' }),
});