/** @type {import('next').NextConfig} */
const nextConfig = () => {
    const rewrites = () => {
        if (process.env.NODE_ENV === "development") {
            return [
                {
                    source: "/api/:path*",
                    destination: "http://localhost:5000/:path*",
                },
                ];
        }else{
            return [
                {
                    source: "/api/:path*",
                    destination: "http://api:5000/:path*",
                },
            ];

        }
    };
    return {
        rewrites,
    };
};


module.exports = nextConfig
