import React from 'react'; // Import React for JSX in TypeScript

export const CallToAction = () => {
  return (
    <div className="bg-black text-white py-[72px] sm:py-24 text-center">
      <div className="container max-w-xl">
        <h2 className="font-bold text-5xl tracking-tighter sm-:text-6xl">Get instant access</h2>
        <p className="text-xl text-white/70 mt-5">
          Join our exclusive community and receive proven trading strategies, market insights, and early access to new features. 100% free, no spam ever.
        </p>
        <form action="" className="mt-10 flex flex-col gap-2.5 max-w-sm mx-auto sm:flex-row">
          <input
            type="email"
            placeholder="your@gmail.com"
            className="h-12 bg-white/20 rounded-lg px-5 font-medium placeholder:text-[#9CA3AF] sm:flex-1"
          />
          <button className="bg-white text-black h-12 rounded-lg px-5">Get access</button>
        </form>
      </div>
    </div>
  )
};