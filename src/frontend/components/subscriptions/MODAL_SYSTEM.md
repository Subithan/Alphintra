# Subscription Modal System

The subscription system has been updated to work as a **modal** that can be opened from anywhere in the application. When opened, it displays over the current page with a blurred background.

## Features

✅ **Modal-based UI** - Opens as an overlay on the current page  
✅ **Backdrop blur** - Background is blurred when modal is open  
✅ **Click outside to close** - Clicking the backdrop closes the modal  
✅ **ESC key to close** - Press Escape to dismiss the modal  
✅ **Scroll lock** - Body scrolling is prevented when modal is open  
✅ **Global state management** - Works from any page in the app  
✅ **Sidebar integration** - Click "Subscriptions" in sidebar to open

## Usage

### From Sidebar
Simply click the "Subscriptions" link in the sidebar. The modal will open on top of your current page.

### From Any Component
Use the `useSubscriptionModal` hook or the `SubscriptionButton` component:

```typescript
// Using the hook
import { useSubscriptionModal } from '@/contexts/SubscriptionModalContext';

function MyComponent() {
  const { openModal } = useSubscriptionModal();

  return (
    <button onClick={openModal}>
      View Plans
    </button>
  );
}
```

```typescript
// Using the pre-built button component
import { SubscriptionButton } from '@/components/subscriptions';

function MyPage() {
  return (
    <div>
      <h1>Trading Engine</h1>
      <SubscriptionButton />
    </div>
  );
}
```

## How It Works

### 1. Context Provider
The `SubscriptionModalProvider` wraps the entire application in `providers.tsx`:

```typescript
<SubscriptionModalProvider>
  {children}
  <SubscriptionModalWrapper />
</SubscriptionModalProvider>
```

### 2. Modal State
The modal state (`isOpen`, `openModal`, `closeModal`) is managed globally via React Context.

### 3. Sidebar Integration
The sidebar item for "Subscriptions" has `isModal: true` flag:

```typescript
{
  id: "subscriptions",
  name: "Subscriptions",
  icon: "solar:card-line-duotone",
  url: "#",
  isModal: true,  // This makes it open as a modal
}
```

### 4. Modal Component
The `SubscriptionModal` component:
- Renders in a portal at the root level
- Uses fixed positioning to overlay the page
- Applies backdrop blur effect
- Handles click-outside and ESC key events
- Prevents body scrolling when open

## Files Structure

```
src/frontend/
├── components/
│   ├── providers.tsx                       # Includes SubscriptionModalProvider
│   ├── subscriptions/
│   │   ├── SubscriptionModal.tsx          # Main modal component
│   │   ├── SubscriptionButton.tsx         # Reusable button to open modal
│   │   └── index.ts                       # Exports
│   └── ui/
│       └── sidebar/
│           ├── sidebarItem.tsx            # Handles modal items
│           ├── sidebarData.ts             # Subscriptions has isModal: true
│           └── types.ts                   # Added isModal property
├── contexts/
│   └── SubscriptionModalContext.tsx       # Global modal state
└── app/
    └── subscriptions/
        └── page.tsx                        # Fallback page (auto-opens modal)
```

## Modal Behavior

### Opening
- Click "Subscriptions" in sidebar → Modal opens
- Navigate to `/subscriptions` → Modal opens, then redirects to dashboard
- Click `<SubscriptionButton />` → Modal opens
- Call `openModal()` → Modal opens

### Closing
- Click backdrop (blurred background) → Modal closes
- Press ESC key → Modal closes
- Click X button in top-right → Modal closes

### Body Scroll Lock
```typescript
useEffect(() => {
  if (isOpen) {
    document.body.style.overflow = 'hidden';  // Lock scroll
  } else {
    document.body.style.overflow = 'unset';   // Restore scroll
  }
}, [isOpen]);
```

## Styling

The modal uses:
- **Backdrop**: `bg-black/50 backdrop-blur-sm`
- **Container**: `max-w-7xl` with responsive padding
- **Content**: `bg-background` with `rounded-2xl` and `shadow-2xl`
- **Scrolling**: `overflow-y-auto` with `max-h-[85vh]`

## Future Enhancements

To add the subscription button on the trading engine page:

```typescript
// In trading engine page
import { SubscriptionButton } from '@/components/subscriptions';

export default function TradingEnginePage() {
  return (
    <div>
      <h1>Trading Engine</h1>
      <p>Upgrade to unlock more features</p>
      <SubscriptionButton />
    </div>
  );
}
```

## TypeScript Types

```typescript
interface SubscriptionModalContextType {
  isOpen: boolean;
  openModal: () => void;
  closeModal: () => void;
}

interface SidebarItemType {
  id: string;
  name: string;
  icon: string;
  url: string;
  external?: boolean;
  isModal?: boolean;  // New property
}
```

## Testing

1. **Test sidebar click**: Click "Subscriptions" in sidebar → Modal should open
2. **Test backdrop click**: Click outside modal → Modal should close
3. **Test ESC key**: Press Escape → Modal should close
4. **Test X button**: Click X in top-right → Modal should close
5. **Test scroll lock**: Modal open → Page should not scroll
6. **Test from button**: Use `<SubscriptionButton />` → Modal should open
7. **Test direct URL**: Navigate to `/subscriptions` → Modal opens, redirects to dashboard

## Notes

- The `/subscriptions` page now just opens the modal and redirects
- Modal state persists until manually closed
- Modal works from any page in the application
- Background blur only works on modern browsers (gracefully degrades)
- Modal is fully responsive and works on mobile devices
