import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => {
    return (
        <div className="min-h-screen flex flex-col items-center justify-center text-white px-6">
            <div className="max-w-2xl mx-auto text-center">
                <div className="mb-8">
                    <img 
                        src="/football.png" 
                        alt="Football" 
                        className="w-32 h-32 mx-auto mb-6 opacity-75" 
                    />
                </div>
                
                <h1 className="text-6xl md:text-8xl font-bold mb-4 text-sky-500">404</h1>
                
                <h2 className="text-2xl md:text-3xl font-semibold mb-4">Page Not Found</h2>
                
                <p className="text-lg md:text-xl text-gray-300 mb-8">
                    Looks like this page got intercepted! The route you're looking for doesn't exist on the field.
                </p>
                
                <Link 
                    to="/" 
                    className="inline-block px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white font-semibold rounded-lg transition-colors duration-300 ease-in-out"
                >
                    Return to Home
                </Link>
            </div>
        </div>
    );
};

export default NotFound;