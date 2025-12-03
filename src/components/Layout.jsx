import React from 'react';
import { Outlet, Link } from 'react-router-dom';
function Layout(){
  return (
    <div className="flex flex-col text-white"> 
      <nav className="flex flex-row justify-between items-center p-2 md:p-4 px-3 md:px-6 my-auto w-screen">
        <Link className=" text-xl md:text-2xl hover:text-gray-700 ease-in-out duration-300" to="/">Home</Link>
        <Link className=" text-xl md:text-2xl hover:text-gray-700 ease-in-out duration-300" to="/enter-team">Enter Team</Link>
      </nav>

      <main>
        <Outlet />
      </main>

      <div>
        <h1>Footer</h1>
      </div>
    </div>
  )
}

export default Layout;