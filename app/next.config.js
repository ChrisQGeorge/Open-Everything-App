/** @type {import('next').NextConfig} */
const nextConfig = () => {
    const rewrites = () => {
        return [
            {
                source: "/api/:path*",
                destination: "http://api:5000/:path*",
            },
        ];
    };
    return {
        rewrites,
    };
};


module.exports = nextConfig
