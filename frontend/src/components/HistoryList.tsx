/**
 * 历史记录列表
 */
import { useState, useEffect } from "react";
import { getHistoryList, deleteHistory, getHistoryDetail } from "../services/api";
import type { HistoryItem, HistoryDetail } from "../services/api";

interface Props {
  onSelect: (detail: HistoryDetail) => void;
  onBack: () => void;
}

export default function HistoryList({ onSelect, onBack }: Props) {
  const [list, setList] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    getHistoryList().then(setList).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("确定删除这条记录？")) return;
    await deleteHistory(id);
    load();
  };

  const handleClick = async (item: HistoryItem) => {
    try {
      const detail = await getHistoryDetail(item.id);
      onSelect(detail);
    } catch {
      alert("无法加载该记录");
    }
  };

  const formatTime = (iso: string) => {
    try { return new Date(iso).toLocaleString("zh-CN"); } catch { return iso; }
  };

  return (
    <div className="history-panel">
      <div className="history-header">
        <button onClick={onBack} className="btn-back">← 返回</button>
        <h3>📋 历史记录</h3>
      </div>

      {loading && <p className="history-loading">加载中...</p>}

      {!loading && list.length === 0 && (
        <div className="history-empty">
          <p>📭 还没有分析记录</p>
          <button onClick={onBack} className="btn-outline">去分析第一份简历</button>
        </div>
      )}

      {!loading && list.length > 0 && (
        <div className="history-list">
          {list.map((item) => (
            <div key={item.id} className="history-item" onClick={() => handleClick(item)}>
              <div className="history-item-main">
                <span className="history-name">{item.candidate_name || "未知"}</span>
                <span className="history-summary">{item.summary_text}</span>
              </div>
              <div className="history-item-meta">
                <span>{formatTime(item.created_at)}</span>
                <span>{item.job_count} 个岗位推荐</span>
                <button className="btn-delete" onClick={(e) => handleDelete(item.id, e)}>🗑</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
