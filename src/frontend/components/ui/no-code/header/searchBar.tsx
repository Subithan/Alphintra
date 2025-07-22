"use client";

const SearchBar = () => {
  return (
    <input
      type="text"
      placeholder="Search..."
      className="px-6 py-2 rounded-full bg-gray-900 text-white text-sm font-medium flex items-center space-x-2 border border-[#262739] transition duration-200 outline-none focus:outline-none"
    />
  );
};

export default SearchBar;