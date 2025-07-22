import React from 'react';

interface ProfileCardProps {
  avatarUrl: string;
  nickname: string;
  uid: string;
  handle: string;
}

const ProfileCard: React.FC<ProfileCardProps> = ({ avatarUrl, nickname, uid, handle }) => {
  return (
    <div className="flex  space-x-4 p-3 pl-10">
      <img
        src={avatarUrl}
        alt={`${nickname}'s avatar`}
        className="w-16 h-16 rounded-full object-cover"
      />
      <div className="flex flex-col">
        <span className="text-lg font-semibold text-black dark:text-white">{nickname}</span>
        <span className="text-sm text-gray-500">UID: {uid}</span>
      </div>
    </div>
  );
};

export default ProfileCard;
