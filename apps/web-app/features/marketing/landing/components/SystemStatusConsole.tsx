"use client";

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Check, Terminal, Activity, ArrowRight } from 'lucide-react';
import Link from 'next/link';

import { Button } from '@/components/ui/button';
import type { StatusSummary } from '../types';

interface SystemStatusConsoleProps {
  statusSummary: StatusSummary | null;
  cta: {
    label: string;
    href: string;
  };
  onCtaClick: () => void;
}

const LOG_LINES = [
  { text: 'Initializing system agents...', delay: 0 },
  { text: 'Connecting to database cluster [primary]...', delay: 400 },
  { text: 'Connection established (12ms)', delay: 800, color: 'text-emerald-400' },
  { text: 'Starting background workers...', delay: 1200 },
  { text: 'Loading AI models (GPT-5, Claude 3.5)...', delay: 1800 },
  { text: 'Models warm and ready', delay: 2400, color: 'text-emerald-400' },
  { text: 'Verifying auth keys (Ed25519)...', delay: 2800 },
  { text: 'System operational.', delay: 3200, color: 'text-emerald-400 font-bold' },
];

export function SystemStatusConsole({ statusSummary, cta, onCtaClick }: SystemStatusConsoleProps) {
  const [lines, setLines] = useState<typeof LOG_LINES>([]);

  useEffect(() => {
    const timers = LOG_LINES.map((line) => {
      return setTimeout(() => {
        setLines((prev) => [...prev, line]);
      }, line.delay);
    });

    return () => timers.forEach(clearTimeout);
  }, []);

  return (
    <div className="w-full max-w-xl overflow-hidden rounded-xl border border-white/10 bg-[#0c0c0c] shadow-2xl backdrop-blur-xl">
      {/* Terminal Header */}
      <div className="flex items-center justify-between border-b border-white/5 bg-white/5 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="h-3 w-3 rounded-full bg-red-500/20 ring-1 ring-red-500/50" />
            <div className="h-3 w-3 rounded-full bg-yellow-500/20 ring-1 ring-yellow-500/50" />
            <div className="h-3 w-3 rounded-full bg-emerald-500/20 ring-1 ring-emerald-500/50" />
          </div>
          <div className="ml-3 flex items-center gap-1.5 rounded-md bg-black/40 px-2 py-0.5">
            <Terminal className="h-3 w-3 text-muted-foreground" />
            <span className="text-[10px] font-medium text-muted-foreground/80">deploy-log</span>
          </div>
        </div>
        
        {statusSummary && (
          <div className="flex items-center gap-2 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[10px] font-medium text-emerald-500 ring-1 ring-emerald-500/20">
            <Activity className="h-3 w-3" />
            {statusSummary.state}
          </div>
        )}
      </div>

      {/* Terminal Body */}
      <div className="p-4 font-mono text-xs leading-relaxed text-muted-foreground/80 min-h-[200px] flex flex-col">
        {lines.map((line, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-start gap-2"
          >
            <span className="shrink-0 text-white/20">{'>'}</span>
            <span className={line.color}>{line.text}</span>
          </motion.div>
        ))}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: [0, 1, 0] }}
          transition={{ repeat: Infinity, duration: 0.8 }}
          className="mt-1 h-4 w-2 bg-emerald-500/50"
        />
        
        <div className="flex-1" />

        {/* Status Footer (integrated into terminal look) */}
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 3.5 }}
          className="mt-6 border-t border-white/5 pt-4 flex items-center justify-between"
        >
          <div className="flex items-center gap-2">
            <div className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-500">
              <Check className="h-3 w-3" />
            </div>
            <span className="text-sm font-medium text-zinc-200">
              {statusSummary?.description || "All systems operational"}
            </span>
          </div>
          
          <Button 
            size="sm" 
            variant="ghost" 
            className="h-8 gap-2 text-xs hover:bg-white/10 hover:text-white"
            onClick={onCtaClick}
            asChild
          >
            <Link href={cta.href}>
              {cta.label}
              <ArrowRight className="h-3 w-3" />
            </Link>
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
