import { useState, useEffect, useRef } from "react"
import { Sidebar } from "@/components/Sidebar"
import { Terminal } from "@/components/Terminal"
import { VideoComposer } from "@/components/VideoComposer"
import { Toaster } from "@/components/ui/toaster"
import { useToast } from "@/hooks/use-toast"

interface LogMessage {
    text: string
    color: string
    timestamp: string
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
    custom_style: boolean
    custom_config: {
        font: string
        primary_color: string
        highlight_color: string
        outline_color: string
        back_color: string
    }
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
        custom_config: {
            font: "Arial",
            primary_color: "#FFFFFF",
            highlight_color: "#00FF00",
            outline_color: "#000000",
            back_color: "#000000"
        }
    })
    const [logs, setLogs] = useState<LogMessage[]>([])
    const [progress, setProgress] = useState(0)
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
                        setClips(prev => [...prev, { filename: data.title, path: data.path }]);
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
                    output_bitrate: config.output_bitrate,
                    start_time: config.start_time,
                    end_time: config.end_time,
                    // Parse resolution string to backend format if needed, or backend handles it
                    output_resolution: config.resolution.includes("x") ? config.resolution : "1080x1920", 
                    
                    // If custom style is enabled, pass the config
                    custom_config: config.custom_style ? {
                        Fontname: config.custom_config.font,
                        PrimaryColour: config.custom_config.primary_color.replace("#", "&H00") + "FF", // Simple AAS mapping (BGR usually, but let's stick to simple hex for now)
                        HighlightColour: config.custom_config.highlight_color.replace("#", "&H00") + "FF",
                        OutlineColour: config.custom_config.outline_color.replace("#", "&H00") + "FF",
                        BackColour: config.custom_config.back_color.replace("#", "&H00") + "FF",
                    } : null
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
            />
            
            <main className="ml-[480px] min-h-screen flex flex-col relative transition-all duration-300 ease-in-out">
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
