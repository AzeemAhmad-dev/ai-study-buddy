"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/text", label: "Text Analytics" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 h-full bg-surface border-r border-thin flex flex-col pt-8 px-4">
      <h1 className="text-xl font-bold text-white mb-10 px-4 tracking-wide uppercase">
        Study<span className="text-neon-blue">Buddy</span>
      </h1>
      <nav className="flex flex-col gap-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`px-4 py-3 rounded-md transition-all duration-300 border-l-2 ${
                isActive
                  ? "border-neon-blue bg-white/5 text-neon-blue font-semibold"
                  : "border-transparent text-gray-400 hover:text-white hover:bg-white/5"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
