import { Button } from '@/components/ui/button';
import { useSubscriptionModal } from '@/contexts/SubscriptionModalContext';

export function SubscriptionButton() {
  const { openModal } = useSubscriptionModal();

  return (
    <Button onClick={openModal} variant="default">
      View Subscriptions
    </Button>
  );
}
