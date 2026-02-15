import { HexColorPicker } from "react-colorful"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { cn } from "@/lib/utils"

interface ColorPickerProps {
    color: string
    onChange: (color: string) => void
    label?: string
    className?: string
    disabled?: boolean
    compact?: boolean // New: compact mode (icon only)
}

export function ColorPicker({ color, onChange, label, className, disabled, compact }: ColorPickerProps) {
    if (disabled) {
        return (
            <div 
                className={cn(
                    "flex items-center space-x-2 bg-zinc-900/50 p-1.5 rounded-lg border border-white/5 opacity-50 cursor-not-allowed w-full",
                    compact && "justify-center w-8 h-8 p-0 rounded-full",
                    className
                )}
            >
                <div 
                    className={cn(
                        "rounded bg-zinc-800 border border-white/10 flex-shrink-0",
                        compact ? "h-4 w-4 rounded-sm" : "h-6 w-6"
                    )}
                    style={{ backgroundColor: color }}
                />
                {!compact && <span className="text-xs text-zinc-500 font-mono truncate flex-1">{color}</span>}
            </div>
        )
    }

    return (
        <Popover>
            <PopoverTrigger asChild>
                <div 
                    className={cn(
                        "flex items-center bg-black/20 hover:bg-black/40 border border-white/5 cursor-pointer transition-colors w-full",
                        compact ? "justify-center p-0 rounded-full w-8 h-8" : "space-x-2 p-1.5 rounded-lg",
                        className
                    )}
                >
                    <div 
                        className={cn(
                            "rounded bg-transparent border border-white/10 shadow-[0_0_10px_rgba(255,255,255,0.05)] flex-shrink-0 relative overflow-hidden group",
                            compact ? "h-4 w-4 rounded-sm" : "h-6 w-6"
                        )}
                        style={{ backgroundColor: color }}
                    >
                         <div className="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                    {!compact && <span className="text-xs text-zinc-400 font-mono truncate flex-1">{color}</span>}
                </div>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-3 bg-zinc-950/95 backdrop-blur-xl border border-white/10 shadow-[0_0_30px_rgba(0,0,0,0.5)] rounded-xl">
                 <div className="space-y-3">
                    <HexColorPicker color={color} onChange={onChange} />
                    <div className="flex justify-between items-center px-1">
                        <label className="text-[10px] uppercase text-zinc-500 font-bold tracking-widest">{label || "Color"}</label>
                        <span className="text-[10px] font-mono text-zinc-400">{color}</span>
                    </div>
                </div>
            </PopoverContent>
        </Popover>
    )
}
