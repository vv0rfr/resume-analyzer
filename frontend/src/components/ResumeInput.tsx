/**
 * 简历输入组件（文本粘贴 / 文件上传）
 */
import { useState } from "react";
import FileUpload from "./FileUpload";

interface Props {
  onSubmit: (content: string, file?: File) => void;
  isLoading: boolean;
}

type InputMode = "text" | "file";

export default function ResumeInput({ onSubmit, isLoading }: Props) {
  const [mode, setMode] = useState<InputMode>("text");
  const [content, setContent] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const charCount = content.length;
  const canSubmit = mode === "file" ? !!file : (charCount >= 10 && charCount <= 50000);

  const handleSubmit = () => {
    if (canSubmit && !isLoading) {
      onSubmit(content, file || undefined);
    }
  };

  const handleClearFile = () => setFile(null);

  return (
    <div className="resume-input">
      <h2>📄 提交简历</h2>

      {/* 模式切换 */}
      <div className="input-mode-tabs">
        <button className={`mode-tab ${mode === "text" ? "active" : ""}`} onClick={() => setMode("text")}>
          粘贴文本
        </button>
        <button className={`mode-tab ${mode === "file" ? "active" : ""}`} onClick={() => setMode("file")}>
          上传文件
        </button>
      </div>

      {/* 文本模式 */}
      {mode === "text" && (
        <>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="请在此粘贴简历文本（最少 10 个字）&#10;&#10;示例：&#10;张三，男，2020年毕业于XX大学计算机科学与技术专业。&#10;3年Java后端开发经验，熟练掌握Spring Boot、MyBatis..."
            rows={15}
            disabled={isLoading}
          />
          <div className="input-footer">
            <span className={`char-count ${charCount > 50000 ? "over" : ""}`}>
              已输入 {charCount} / 50000 字
            </span>
          </div>
        </>
      )}

      {/* 文件模式 */}
      {mode === "file" && (
        <div className="file-mode-area">
          <FileUpload onFile={setFile} onClear={handleClearFile} fileName={file?.name || null} disabled={isLoading} />
        </div>
      )}

      {/* 提交按钮 */}
      <div className="input-footer">
        <span />
        <button onClick={handleSubmit} disabled={!canSubmit || isLoading}>
          {isLoading ? "⏳ 分析中..." : "🔍 开始分析"}
        </button>
      </div>
    </div>
  );
}
