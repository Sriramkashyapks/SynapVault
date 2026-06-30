"use client";

import { useEffect, useState, useRef } from "react";

interface SystemHealth {
  status: string;
  database: string;
}

interface IngestedDoc {
  id: string;
  filename: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
}

export default function Dashboard() {
  // System Health States
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);

  // Ingestion States
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [file, setFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [processingDoc, setProcessingDoc] = useState<IngestedDoc | null>(null);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const apiURL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // 1. Fetch System Health
  const fetchHealth = async () => {
    setHealthLoading(true);
    try {
      const response = await fetch(`${apiURL}/health`);
      if (response.ok) {
        const data = await response.json();
        setHealth(data);
      } else {
        setHealth(null);
      }
    } catch {
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  // 2. Drag & Drop Handlers
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  // 3. File Validation
  const validateAndSetFile = (selectedFile: File) => {
    setNotification(null);
    // Enforce PDF only
    if (selectedFile.type !== "application/pdf" && !selectedFile.name.toLowerCase().endsWith(".pdf")) {
      showNotification("error", "Unsupported format. Only PDF files are allowed.");
      return;
    }
    // Enforce size limit (2 MB = 2,097,152 bytes)
    if (selectedFile.size > 2 * 1024 * 1024) {
      showNotification("error", "File exceeds 2 MB size limit.");
      return;
    }
    setFile(selectedFile);
  };

  const showNotification = (type: "success" | "error", message: string) => {
    setNotification({ type, message });
    setTimeout(() => setNotification(null), 5000);
  };

  // 4. File Upload & Status Polling
  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setUploadProgress(10);
    setNotification(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Simulate fake progress bar during initial fetch
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => (prev >= 90 ? 90 : prev + 10));
      }, 100);

      const response = await fetch(`${apiURL}/api/v1/documents/upload`, {
        method: "POST",
        body: formData,
      });

      clearInterval(progressInterval);

      if (!response.ok) {
        let errorMessage = "Upload failed";
        try {
          const errorJson = await response.json();
          errorMessage = errorJson.detail || "Upload failed";
        } catch {
          try {
            errorMessage = await response.text();
          } catch {
            errorMessage = "Upload failed";
          }
        }
        throw new Error(errorMessage);
      }


      const data = await response.json();
      setUploadProgress(100);

      // Initialize Polling state
      setProcessingDoc({
        id: data.document_id,
        filename: data.filename,
        status: data.status,
      });

      showNotification("success", "File uploaded successfully! Starting PDF analysis.");
      setFile(null); // Clear React state
      if (fileInputRef.current) {
        fileInputRef.current.value = ""; // Reset HTML DOM input element
      }

      // Start background status check
      pollDocumentStatus(data.document_id);

    } catch (err: any) {
      showNotification("error", err.message || "Connection to API failed.");
      setIsUploading(false);
    }
  };

  const pollDocumentStatus = (docId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`${apiURL}/api/v1/documents/${docId}`);
        if (!response.ok) return;

        const data = await response.json();

        setProcessingDoc({
          id: data.document_id,
          filename: data.filename,
          status: data.status,
        });

        // Stop polling when status resolves to COMPLETED or FAILED
        if (data.status === "COMPLETED") {
          clearInterval(pollInterval);
          showNotification("success", `Successfully ingested and parsed "${data.filename}"!`);
          setIsUploading(false);
          setProcessingDoc(null);
        } else if (data.status === "FAILED") {
          clearInterval(pollInterval);
          showNotification("error", `Failed parsing "${data.filename}". Please verify file content.`);
          setIsUploading(false);
          setProcessingDoc(null);
        }

      } catch (err) {
        console.error("Polling error:", err);
      }
    }, 2000); // Check status every 2 seconds
  };

  return (
    <div className="space-y-8">
      {/* Toast Notifications */}
      {notification && (
        <div className={`fixed top-6 right-6 px-5 py-3 rounded-lg shadow-xl z-50 transition border animate-fade-in ${notification.type === "success"
          ? "bg-green-950/90 text-green-300 border-green-800"
          : "bg-red-950/90 text-red-300 border-red-800"
          }`}>
          <div className="flex items-center gap-2 text-sm font-medium">
            <span>{notification.type === "success" ? "✅" : "⚠️"}</span>
            {notification.message}
          </div>
        </div>
      )}

      {/* Info banner */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-indigo-900/40 via-purple-900/20 to-zinc-900 border border-zinc-800">
        <h2 className="text-2xl font-bold tracking-tight text-white mb-2">Ingestion Engine Panel</h2>
        <p className="text-zinc-400 max-w-xl text-sm leading-relaxed">
          Upload PDF files (Max 2 MB) to extract document text. The parser runs asynchronously in the background.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* DRAG AND DROP FILE UPLOADER */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/10 backdrop-blur-sm">
            <h3 className="text-white font-semibold text-lg mb-4">Upload PDF Document</h3>

            {/* Drag Area */}
            <div
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center cursor-pointer transition ${dragActive
                ? "border-indigo-500 bg-indigo-500/5"
                : "border-zinc-800 hover:border-zinc-700 bg-zinc-950/40"
                }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                accept=".pdf"
                onChange={handleFileInputChange}
                disabled={isUploading}
              />

              <span className="text-4xl mb-4">📥</span>
              <p className="text-sm font-medium text-zinc-300">
                Drag & Drop your PDF file here, or <span className="text-indigo-400 underline">browse</span>
              </p>
              <p className="text-xs text-zinc-500 mt-2">Maximum file size: 2 MB (.pdf format only)</p>
            </div>

            {/* Selected File Details */}
            {file && (
              <div className="mt-4 p-4 rounded-lg bg-zinc-950 border border-zinc-800 flex items-center justify-between animate-fade-in">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">📄</span>
                  <div>
                    <p className="text-sm font-medium text-white truncate max-w-[200px] md:max-w-xs">{file.name}</p>
                    <p className="text-xs text-zinc-500">{(file.size / 1024).toFixed(1)} KB</p>
                  </div>
                </div>
                <button
                  onClick={handleUpload}
                  disabled={isUploading}
                  className="px-4 py-2 rounded-lg bg-indigo-600 text-white font-medium text-xs hover:bg-indigo-500 transition disabled:opacity-50"
                >
                  🚀 Start Ingestion
                </button>
              </div>
            )}

            {/* Upload Progress Bar */}
            {isUploading && (
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-indigo-400 flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 animate-ping"></span>
                    Uploading PDF...
                  </span>
                  <span className="text-zinc-400">{uploadProgress}%</span>
                </div>
                <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-500 h-full rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>

          {/* BACKGROUND PROCESSING SPINNER */}
          {processingDoc && (
            <div className="p-6 rounded-xl border border-indigo-900/60 bg-indigo-950/10 flex items-center gap-5 animate-pulse">
              <div className="w-10 h-10 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
              <div>
                <h4 className="text-white font-semibold text-sm">Processing Document Structure</h4>
                <p className="text-xs text-zinc-400 mt-1">
                  Parsing pages of <span className="font-semibold text-zinc-200">"{processingDoc.filename}"</span> using LangChain. Status: <span className="text-indigo-300 font-bold">{processingDoc.status}</span>
                </p>
              </div>
            </div>
          )}
        </div>

        {/* SYSTEM STATUS CARD (PHASE 1 INTEGRATION) */}
        <div className="space-y-6">
          <div className="p-6 rounded-xl border border-zinc-800 bg-zinc-900/10">
            <h3 className="text-white font-semibold text-base mb-4">Core Infrastructure Status</h3>
            <div className="space-y-4">

              {/* API CARD */}
              <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-zinc-500 uppercase tracking-wider">FastAPI Core</span>
                  {healthLoading ? (
                    <span className="text-[10px] text-zinc-500 animate-pulse">Checking...</span>
                  ) : health ? (
                    <span className="text-[10px] text-green-400 flex items-center gap-1">🟢 Active</span>
                  ) : (
                    <span className="text-[10px] text-red-500 flex items-center gap-1">🔴 Offline</span>
                  )}
                </div>
                <p className="text-lg font-bold text-white">{healthLoading ? "..." : health ? "Online" : "Connection Refused"}</p>
              </div>

              {/* DB CARD */}
              <div className="p-4 rounded-lg bg-zinc-950 border border-zinc-900">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-zinc-500 uppercase tracking-wider">Postgres Vector</span>
                  {healthLoading ? (
                    <span className="text-[10px] text-zinc-500 animate-pulse">Checking...</span>
                  ) : health?.database === "connected" ? (
                    <span className="text-[10px] text-green-400 flex items-center gap-1">🟢 Connected</span>
                  ) : (
                    <span className="text-[10px] text-red-500 flex items-center gap-1">🔴 Disconnected</span>
                  )}
                </div>
                <p className="text-lg font-bold text-white">
                  {healthLoading ? "..." : health?.database === "connected" ? "pgvector Active" : "Offline"}
                </p>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
