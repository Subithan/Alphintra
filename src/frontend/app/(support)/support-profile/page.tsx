import BalanceCard from "@/components/ui/user/dashboard/BalanceCard";
import ProfileCard from "@/components/ui/user/profile/profileCard";
import { VerifyStepper } from "@/components/ui/user/profile/verifyStepper";

export default function Profile() {
  return (
    <div className="min-h-screen flex flex-col gap-6 px-4 py-6 md:px-8 lg:px-14">
      <ProfileCard
        avatarUrl="/images/profile/user-1.jpg"
        nickname="Odette Amrhei"
        uid="1115893081"
        handle="nJM7y"
      />
    </div>
  );
}
