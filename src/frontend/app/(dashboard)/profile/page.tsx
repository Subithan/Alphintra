import BalanceCard from "@/components/ui/dashboard/BalanceCard";
import ProfileCard from "@/components/ui/profile/profileCard";
import { VerifyStepper } from "@/components/ui/profile/verifyStepper";

export default function Profile() {
  return (
    <div className="min-h-screen flex flex-col gap-6 px-4 py-6 md:px-8 lg:px-14">
      <ProfileCard
        avatarUrl="/images/profile/user-1.jpg"
        nickname="Odette Amrhei"
        uid="1115893081"
        handle="nJM7y"
      />

      <VerifyStepper />
      <div className="md:rounded-3xl  rounded-2xl border border-border bg-card p-6 md:ml-4 md:mr-7 mx-6">
        <BalanceCard />
      </div>
    </div>
  );
}
