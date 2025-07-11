const { useState } = React;

// BBCode 解析器
function parseBBCode(text) {
    if (!text) return '';
    
    let html = text;
    
    // 转义HTML特殊字符（除了我们要处理的BBCode）
    html = html.replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;');
    
    // 处理图片标签 [img]url[/img]
    html = html.replace(/\[img\](.*?)\[\/img\]/gi, '<img src="$1" alt="poster" style="max-width: 200px; height: auto; border-radius: 8px; margin: 10px 0;" />');
    
    // 处理嵌套的粗体和颜色标签 [b][color=xxx]text[/color][/b]
    html = html.replace(/\[b\]\[color=([^\]]+)\](.*?)\[\/color\]\[\/b\]/gi, '<strong style="color: $1;">$2</strong>');
    
    // 处理嵌套的颜色和粗体标签 [color=xxx][b]text[/b][/color]
    html = html.replace(/\[color=([^\]]+)\]\[b\](.*?)\[\/b\]\[\/color\]/gi, '<strong style="color: $1;">$2</strong>');
    
    // 处理单独的粗体标签 [b]text[/b]
    html = html.replace(/\[b\](.*?)\[\/b\]/gi, '<strong>$1</strong>');
    
    // 处理单独的颜色标签 [color=xxx]text[/color]
    html = html.replace(/\[color=([^\]]+)\](.*?)\[\/color\]/gi, '<span style="color: $1;">$2</span>');
    
    // 处理换行 - 保留原有的换行格式
    html = html.replace(/\n/g, '<br>');
    
    // 处理全角空格，保持对齐
    html = html.replace(/　/g, '&nbsp;&nbsp;');
    
    return html;
}

function TMDBApp() {
    const [tmdbLink, setTmdbLink] = useState('');
    const [seasonNumber, setSeasonNumber] = useState('');
    const [result, setResult] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!tmdbLink.trim()) {
            setError('请输入 TMDB 链接');
            setSuccess('');
            return;
        }

        setIsLoading(true);
        setError('');
        setSuccess('');
        setResult('');

        try {
            // 构建请求 URL (使用相对路径，nginx 会代理到后端)
            const params = new URLSearchParams({
                media_link: tmdbLink.trim(),
                language: 'zh-CN'
            });
            
            if (seasonNumber.trim()) {
                params.append('season_number', seasonNumber.trim());
            }

            const response = await fetch(`/introduction?${params.toString()}`);
            
            if (response.ok) {
                // 检查响应内容类型
                const contentType = response.headers.get('content-type');
                
                if (contentType && contentType.includes('application/json')) {
                    // JSON 响应，表示错误
                    const errorData = await response.json();
                    setError(errorData.message || '获取失败');
                } else {
                    // 纯文本响应，表示成功
                    const text = await response.text();
                    setResult(text);
                    setSuccess('影视信息获取成功！');
                }
            } else {
                // HTTP 错误状态码
                try {
                    const errorData = await response.json();
                    setError(errorData.message || `请求失败 (${response.status})`);
                } catch {
                    setError(`请求失败 (${response.status})`);
                }
            }
        } catch (err) {
            console.error('请求错误:', err);
            setError('网络请求失败，请检查后端服务是否正常运行');
        } finally {
            setIsLoading(false);
        }
    };

    const copyToClipboard = async (content, type = 'BBCode') => {
        if (!content) return;
        
        try {
            await navigator.clipboard.writeText(content);
            setSuccess(`${type}内容已复制到剪贴板！`);
            setError('');
            
            // 3秒后清除成功消息
            setTimeout(() => setSuccess(''), 3000);
        } catch (err) {
            setError('复制失败，请手动选择复制');
        }
    };

    const copyAsHTML = async () => {
        if (!result) return;
        
        const htmlContent = parseBBCode(result);
        await copyToClipboard(htmlContent, 'HTML');
    };

    return (
        <div className="app-container">
            {/* 导航栏 */}
            <div className="navbar">
                <div className="navbar-left">TMDB Gen</div>
                <div className="navbar-right">
                    <a href="https://github.com/Pixel-LH/TMDBGen" target="_blank" rel="noopener noreferrer" className="navbar-link">Github</a>
                    <span className="navbar-link">Powered By TMDB</span>
                </div>
            </div>

            {/* 主要内容 */}
            <div className="main-content">
                <p className="description">
                    TMDB 影视链接解析工具，支持电影和电视剧的简介信息生成
                </p>

                {/* 输入区域 */}
                <div className="input-section">
                    <form onSubmit={handleSubmit}>
                        <div className="input-row">
                            <div className="input-group">
                                <label htmlFor="tmdbLink" className="label">
                                    TMDB 链接 *
                                </label>
                                <input
                                    type="url"
                                    id="tmdbLink"
                                    className="input"
                                    value={tmdbLink}
                                    onChange={(e) => setTmdbLink(e.target.value)}
                                    placeholder="https://www.themoviedb.org/movie/550"
                                    required
                                />
                            </div>

                            <div className="input-group-small">
                                <label htmlFor="seasonNumber" className="label">
                                    剧集季度 <span className="input-optional">(可选)</span>
                                </label>
                                <input
                                    type="number"
                                    id="seasonNumber"
                                    className="input"
                                    value={seasonNumber}
                                    onChange={(e) => setSeasonNumber(e.target.value)}
                                    placeholder="1"
                                    min="1"
                                />
                            </div>

                            <button 
                                type="submit" 
                                className="btn btn-primary"
                                disabled={isLoading}
                            >
                                {isLoading && <div className="loading-spinner"></div>}
                                {isLoading ? '查询中...' : '查询'}
                            </button>
                        </div>
                    </form>
                </div>

                {/* 结果区域 */}
                <div className="result-section">
                    <div className="result-header">
                        <h3 className="result-label">输出结果</h3>
                    </div>
                    
                    <div className="result-content">
                        {/* 原始文本面板 */}
                        <div className="result-panel">
                            <div className="panel-header">
                                <h4 className="panel-title">BBCode 源码</h4>
                                <button 
                                    className="btn btn-secondary"
                                    onClick={() => copyToClipboard(result)}
                                    disabled={!result}
                                >
                                    复制 BBCode
                                </button>
                            </div>
                            <textarea
                                className={`result-textarea ${result ? 'has-content' : ''}`}
                                value={result}
                                readOnly
                                placeholder="点击查询按钮后，生成的 BBCode 将显示在这里..."
                            />
                        </div>

                        {/* 预览面板 */}
                        <div className="result-panel">
                            <div className="panel-header">
                                <h4 className="panel-title">实时预览</h4>
                                <button 
                                    className="btn btn-secondary"
                                    onClick={copyAsHTML}
                                    disabled={!result}
                                >
                                    复制 HTML
                                </button>
                            </div>
                            {result ? (
                                <div 
                                    className="preview-area"
                                    dangerouslySetInnerHTML={{
                                        __html: parseBBCode(result)
                                    }}
                                />
                            ) : (
                                <div className="preview-area empty">
                                    预览将在这里显示渲染后的结果...
                                </div>
                            )}
                        </div>
                    </div>
                    
                    {error && (
                        <div className="error-message">
                            {error}
                        </div>
                    )}
                    
                    {success && (
                        <div className="success-message">
                            {success}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// 渲染应用
ReactDOM.render(<TMDBApp />, document.getElementById('root')); 