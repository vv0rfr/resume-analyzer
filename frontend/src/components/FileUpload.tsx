/**
 * 文件拖拽上传组件
 */
import { useState, useRef, type DragEvent, type ChangeEvent } from "react";

interface Props {
  onFile: (file: File) => void;
  onClear: () => void;
  fileName: string | null;
  disabled: boolean;
}

const ALLOWED = [".pdf", ".docx", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];

export default function FileUpload({ onFile, onClear, fileName, disabled }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = (f: File): boolean => {
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED.includes(f.type) && !ALLOWED.includes(ext)) {
      setError("仅支持 PDF 和 Word (.docx) 文件");
      return false;
    }
    if (f.size > 10 * 1024 * 1024) {
      setError("文件大小不能超过 10MB");
      return false;
    }
    setError(null);
    return true;
  };

  const handleFile = (f: File) => {
    if (validate(f)) onFile(f);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  return (
    <div className="file-upload-area">
      {fileName ? (
        <div className="file-selected">
          <span>📎 {fileName}</span>
          <button onClick={onClear} disabled={disabled} className="file-clear">✕ 清除</button>
        </div>
      ) : (
        <div
          className={`file-dropzone ${dragOver ? "drag-over" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <span className="drop-icon">📂</span>
          <p>拖拽简历文件到此处，或点击选择文件</p>
          <p className="drop-hint">支持 PDF / Word (.docx)，最大 10MB</p>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx"
            onChange={handleChange}
            hidden
            disabled={disabled}
          />
        </div>
      )}
      {error && <p className="file-error">{error}</p>}
    </div>
  );
}
