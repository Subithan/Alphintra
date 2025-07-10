"use client";

const SearchBar = () => {
  return (
    <input
      type="text"
      placeholder="Search..."
      className="px-6 py-2 rounded-full text-sm font-medium border transition duration-200 outline-none
        bg-gray-100 text-black border-gray-300 
        dark:bg-gray-900 dark:text-white dark:border-[#262739]"
    />
  );
};

export default SearchBar;
