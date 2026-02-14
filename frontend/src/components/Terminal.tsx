import { ScrollArea } from "@/components/ui/scroll-area"
import { useEffect, useRef } from "react"
import { AlertTriangle, CheckCircle, Info, Link, Zap } from "lucide-react"

interface LogMessage {
    text: string
    color: string
    timestamp: string
}

export function Terminal({ logs }: { logs: LogMessage[] }) {
    const scrollRef = useRef<HTMLDivElement>(null)

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollIntoView({ behavior: "smooth" })
        }
    }, [logs])

    const getIcon = (text: string, color: string) => {
        if (text.includes("❌") || color.includes("red")) return <AlertTriangle className="h-3 w-3 text-red-500 mt-0.5 flex-shrink-0" />
        if (text.includes("✅") || color.includes("green")) return <CheckCircle className="h-3 w-3 text-green-500 mt-0.5 flex-shrink-0" />
        if (text.includes("🔗") || color.includes("blue")) return <Link className="h-3 w-3 text-blue-400 mt-0.5 flex-shrink-0" />
        if (text.includes("🧠") || color.includes("purple")) return <Zap className="h-3 w-3 text-purple-400 mt-0.5 flex-shrink-0" />
        return <Info className="h-3 w-3 text-zinc-600 mt-0.5 flex-shrink-0" />
    }

    return (
        <div className="flex flex-col h-64 bg-black border-t border-zinc-800">
            <div className="flex items-center justify-between px-4 py-2 border-b border-zinc-900 bg-zinc-950">
                <span className="text-xs font-mono text-zinc-500">TERMINAL OUTPUT</span>
                <div className="flex space-x-1">
                    <div className="h-2 w-2 rounded-full bg-zinc-800"></div>
                    <div className="h-2 w-2 rounded-full bg-zinc-800"></div>
                    <div className="h-2 w-2 rounded-full bg-zinc-800"></div>
                </div>
            </div>
            <ScrollArea className="flex-1 p-4">
                <div className="space-y-1 font-mono text-xs">
                    {logs.map((log, i) => (
                        <div key={i} className={`flex space-x-2 ${log.color}`}>
                            {getIcon(log.text, log.color)}
                            <span className="break-all">{log.text}</span>
                        </div>
                    ))}
                    <div ref={scrollRef} />
                </div>
            </ScrollArea>
        </div>
    )
}
