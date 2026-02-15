import { useState, useEffect, useRef } from "react"
import { Sidebar } from "@/components/Sidebar"
import { Terminal } from "@/components/Terminal"
import { VideoComposer } from "@/components/VideoComposer"
import { Toaster } from "@/components/ui/toaster"
import { useToast } from "@/hooks/use-toast"
import { Switch } from "@/components/ui/switch"
import { Label } from "@/components/ui/label"

interface LogMessage {
    text: string
    color: string
    timestamp: string
}

export interface Clip {
    filename: string
    path: string
    thumbnail?: string
    score?: number
    source_path?: string
    start_time?: number
    end_time?: number
}

export interface VideoConfig {
    url: string
    style: string
    resolution: string
    min_sec: number
    max_sec: number
    content_type: string
    focus_mode: string
    caption_pos: string
    caption_size: number
    output_bitrate: string
    start_time: string
    end_time: string
    use_b_roll: boolean
    use_split_screen: boolean
    custom_style: boolean
    stroke_enabled: boolean
    back_enabled: boolean
    stroke_width: number
    back_alpha: number
    outline_color: string
    back_color: string
    custom_config: {
        font: string
        primary_color: string
        highlight_color: string
    }
}

// Helper: Convert Hex (#RRGGBB) to ASS BGR (&H00BBGGRR)
const hexToAss = (hex: string) => {
    hex = hex.replace("#", "");
    if (hex.length === 3) {
        hex = hex.split('').map(c => c + c).join('');
    }
    if (hex.length !== 6) return "&H00FFFFFF";
    
    const r = hex.substring(0, 2);
    const g = hex.substring(2, 4);
    const b = hex.substring(4, 6);
    
    // ASS Format: &H[Alpha][Blue][Green][Red]
    // We assume fully opaque (00) for now, user can tweak alpha in advanced if needed
    return `&H00${b}${g}${r}`;
}

function App() {
    const [config, setConfig] = useState<VideoConfig>({
        url: "",
        style: "Hormozi",
        resolution: "1080p",
        min_sec: 15,
        max_sec: 60,
        content_type: "Podcast",
        focus_mode: "auto-face",
        caption_pos: "center",
        caption_size: 60,
        output_bitrate: "5000k",
        start_time: "0",
        end_time: "",
        custom_style: false,
        stroke_enabled: false,
        back_enabled: false,
        stroke_width: 3,
        back_alpha: 0.5,
        outline_color: "#000000",
        back_color: "#000000",
        custom_config: {
            font: "Arial",
            primary_color: "#FFFFFF",
            highlight_color: "#00FF00"
        },
        use_b_roll: true,
        use_split_screen: true
    })
    const [logs, setLogs] = useState<LogMessage[]>([])
    const [progress, setProgress] = useState(0)
    const [progressPhase, setProgressPhase] = useState<{name: string, percent: number, text: string} | null>(null)
    const [isProcessing, setIsProcessing] = useState(false)
    const [isFetchingMetadata, setIsFetchingMetadata] = useState(false)
    const [videoMetadata, setVideoMetadata] = useState<{title: string, duration: number} | null>(null)
    const [clips, setClips] = useState<any[]>([])
    const { toast } = useToast()
    const wsRef = useRef<WebSocket | null>(null)

    // Connect WebSocket
    // Connect WebSocket with Auto-Reconnect
    useEffect(() => {
        let ws: WebSocket | null = null;
        let retryTimeout: NodeJS.Timeout;

        const connect = () => {
            ws = new WebSocket("ws://127.0.0.1:8000/ws");
            wsRef.current = ws;

            ws.onopen = () => {
                setLogs(prev => [...prev, { text: "🔌 Connected to Engine Core", color: "text-green-500", timestamp: new Date().toLocaleTimeString() }]);
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === "log") {
                        setLogs(prev => [...prev, {
                            text: data.text,
                            color: data.color || "text-zinc-400",
                            timestamp: new Date().toLocaleTimeString()
                        }]);
                    } else if (data.type === "progress") {
                        setProgress(data.progress * 100);
                    } else if (data.type === "clip_ready") {
                        setClips(prev => [...prev, { 
                            filename: data.title, 
                            path: data.path,
                            thumbnail: data.thumbnail,
                            score: data.score,
                            source_path: data.source_path,
                            start_time: data.start_time,
                            end_time: data.end_time
                        }]);
                    } else if (data.type === "status") {
                        // NEW: Handle pipeline status updates
                        if (data.state === "success") {
                            setIsProcessing(false)
                            setProgress(100)
                            toast({ title: "Process Complete", description: "All clips generated successfully.", className: "bg-green-900 border-green-800 text-green-100" })
                        } else if (data.state === "error") {
                            setIsProcessing(false)
                            toast({ title: "Process Failed", description: data.message, variant: "destructive" })
                        } else if (data.state === "cancelled") {
                            setIsProcessing(false)
                            setProgress(0)
                            setProgressPhase(null)
                            toast({ title: "Cancelled", description: "Operation was cancelled by user.", className: "bg-orange-900 border-orange-800 text-orange-100" })
                        }
                    } else if (data.type === "progress_rich") {
                        setProgress(data.progress * 100);
                        setProgressPhase({
                            name: data.phase,
                            percent: data.phase_progress * 100,
                            text: data.text
                        });
                    }
                } catch (e) {
                    console.error("WS Parse Error", e);
                }
            };

            ws.onclose = () => {
                setLogs(prev => [...prev, { text: "❌ Disconnected. Retrying in 3s...", color: "text-red-500", timestamp: new Date().toLocaleTimeString() }]);
                // Retry connection
                retryTimeout = setTimeout(connect, 3000);
            };

            ws.onerror = (err) => {
                console.error("WS Error", err);
                ws?.close();
            };
        };

        connect();

        return () => {
            if (ws) ws.close();
            clearTimeout(retryTimeout);
        };
    }, []);

    const handleFetchMetadata = async () => {
        if (!config.url) return
        setIsFetchingMetadata(true)
        try {
            const res = await fetch("http://127.0.0.1:8000/metadata", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url: config.url })
            })
            const data = await res.json()
            if (data.status === "success") {
                setVideoMetadata({ title: data.title, duration: data.duration })
                // Update end_time if not set
                if (!config.end_time) {
                    setConfig(prev => ({ ...prev, end_time: data.duration.toString() }))
                }
            } else {
                toast({ title: "Fetch Failed", description: data.message, variant: "destructive" })
            }
        } catch (e) {
            toast({ title: "Connection Failed", description: "Could not reach backend.", variant: "destructive" })
        } finally {
            setIsFetchingMetadata(false)
        }
    }

    const handleProcess = async () => {
        if (!config.url) return
        
        setIsProcessing(true)
        setProgress(0)
        setLogs([]) // Clear logs

        try {
            const res = await fetch("http://127.0.0.1:8000/process", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    url: config.url,
                    style: config.style,
                    resolution: config.resolution,
                    min_sec: config.min_sec,
                    max_sec: config.max_sec,
                    content_type: config.content_type,
                    focus_region: config.focus_mode,
                    caption_pos: config.caption_pos,
                    caption_size: config.caption_size,
                    output_bitrate: config.output_bitrate,
                    start_time: config.start_time,
                    end_time: config.end_time,
                    use_b_roll: config.use_b_roll,
                    use_split_screen: config.use_split_screen,
                    // Parse resolution string to backend format if needed, or backend handles it
                    output_resolution: config.resolution.includes("x") ? config.resolution : "1080x1920", 
                    
                    // If custom style is enabled, pass the full config, otherwise just overrides
                    custom_config: config.custom_style ? {
                        Fontname: config.custom_config.font,
                        PrimaryColour: hexToAss(config.custom_config.primary_color),
                        HighlightColour: hexToAss(config.custom_config.highlight_color),
                        OutlineColour: config.stroke_enabled 
                            ? hexToAss(config.outline_color) 
                            : "&H00000000",
                        BackColour: config.back_enabled
                            ? (() => {
                                const hex = config.back_color.replace("#", "")
                                const alpha = Math.floor((1 - config.back_alpha) * 255).toString(16).padStart(2, '0').toUpperCase()
                                return `&H${alpha}${hex.slice(4,6)}${hex.slice(2,4)}${hex.slice(0,2)}`
                              })()
                            : "&HFF000000",
                        BorderStyle: config.back_enabled ? 3 : 1,
                        Outline: config.stroke_enabled ? config.stroke_width : 0,
                    } : {
                        // Global overrides for presets
                        OutlineColour: config.stroke_enabled ? hexToAss(config.outline_color) : undefined,
                        BackColour: config.back_enabled ? (() => {
                            const hex = config.back_color.replace("#", "")
                            const alpha = Math.floor((1 - config.back_alpha) * 255).toString(16).padStart(2, '0').toUpperCase()
                            return `&H${alpha}${hex.slice(4,6)}${hex.slice(2,4)}${hex.slice(0,2)}`
                        })() : undefined,
                        ...(config.back_enabled ? { BorderStyle: 3 } : { BorderStyle: 1 }),
                        Outline: config.stroke_enabled ? config.stroke_width : 0
                    }
                })
            })
            
            const data = await res.json()
            if (data.status === "error") {
                toast({
                    title: "Error",
                    description: data.message,
                    variant: "destructive"
                })
                setIsProcessing(false)
            }
        } catch (e) {
            toast({
                title: "Connection Failed",
                description: "Could not start processing.",
                variant: "destructive"
            })
            setIsProcessing(false)
        }
    }

    const handleCancel = async () => {
        try {
            await fetch("http://127.0.0.1:8000/cancel", { method: "POST" })
        } catch (e) {
            console.error(e)
        }
    }

    return (
        <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/30">
            <Sidebar 
                config={config}
                setConfig={setConfig}
                onProcess={handleProcess} 
                onCancel={handleCancel}
                onFetchMetadata={handleFetchMetadata}
                isProcessing={isProcessing}
                isFetchingMetadata={isFetchingMetadata}
                videoMetadata={videoMetadata}
                progress={progress}
                progressPhase={progressPhase}
            />
            
            <main className="ml-[500px] min-h-screen flex flex-col relative transition-all duration-300 ease-in-out">
                <div className="flex-1 p-8 overflow-y-auto">
                     <VideoComposer clips={clips} />
                </div>
                <Terminal logs={logs} />
            </main>
            
            <Toaster />
        </div>
    )
}

export default App
