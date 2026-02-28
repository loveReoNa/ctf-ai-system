#!/usr/bin/env python3
"""
结果分析和报告生成模块
负责分析攻击执行结果，生成详细的报告和可视化数据
"""

import json
import time
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from src.utils.logger import logger


@dataclass
class AnalysisResult:
    """分析结果"""
    vulnerabilities: List[Dict[str, Any]] = field(default_factory=list)
    security_risks: List[Dict[str, Any]] = field(default_factory=list)
    flags_found: List[str] = field(default_factory=list)
    success_rate: float = 0.0
    execution_time: float = 0.0
    confidence: float = 0.0
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ReportSection:
    """报告部分"""
    title: str
    content: str
    level: int = 1  # 标题级别


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: str = "reports"):
        """
        初始化报告生成器
        
        Args:
            output_dir: 报告输出目录
        """
        self.logger = logger.getChild("report_generator")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # 报告模板
        self.templates = {
            "html": self._generate_html_report,
            "markdown": self._generate_markdown_report,
            "json": self._generate_json_report,
            "text": self._generate_text_report
        }
        
        self.logger.info(f"报告生成器初始化完成，输出目录: {self.output_dir}")
    
    def analyze_execution_results(self, execution_report: Dict[str, Any]) -> AnalysisResult:
        """
        分析执行结果
        
        Args:
            execution_report: 执行报告
            
        Returns:
            分析结果
        """
        self.logger.info("开始分析执行结果")
        
        result = AnalysisResult()
        
        try:
            # 提取基本信息
            challenge = execution_report.get("challenge", {})
            execution_summary = execution_report.get("execution_summary", {})
            step_details = execution_report.get("step_details", [])
            security_assessment = execution_report.get("security_assessment", {})
            
            # 分析漏洞
            result.vulnerabilities = security_assessment.get("vulnerabilities_found", [])
            
            # 分析安全风险
            result.security_risks = self._analyze_security_risks(step_details)
            
            # 提取flag
            result.flags_found = execution_report.get("flags", [])
            
            # 计算成功率
            stats = execution_summary.get("statistics", {})
            total_steps = stats.get("total_steps", 0)
            successful_steps = stats.get("successful_steps", 0)
            result.success_rate = successful_steps / total_steps if total_steps > 0 else 0.0
            
            # 执行时间
            result.execution_time = execution_summary.get("total_time", 0.0)
            
            # 置信度
            result.confidence = security_assessment.get("confidence", 0.0)
            
            # 生成建议
            result.recommendations = self._generate_analysis_recommendations(
                result.vulnerabilities,
                result.security_risks,
                result.success_rate
            )
            
            self.logger.info(f"分析完成: 发现 {len(result.vulnerabilities)} 个漏洞, "
                           f"{len(result.flags_found)} 个flag, 成功率: {result.success_rate:.2%}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"结果分析失败: {e}")
            return result
    
    def _analyze_security_risks(self, step_details: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析安全风险"""
        risks = []
        
        for step in step_details:
            if step.get("tool") == "nmap_scan" and step.get("status") == "success":
                # 从步骤输出中提取风险信息
                output = step.get("output", {})
                analysis = output.get("analysis", {})
                security_risks = analysis.get("security_risks", [])
                
                for risk in security_risks:
                    risks.append({
                        "type": "Open Port",
                        "description": risk,
                        "severity": self._assess_risk_severity(risk),
                        "step": step.get("step_id")
                    })
            
            elif step.get("tool") == "sqlmap_scan" and step.get("status") == "success":
                output = step.get("output", {})
                analysis = output.get("analysis", {})
                
                if analysis.get("injection_found", False):
                    risks.append({
                        "type": "SQL Injection",
                        "description": f"发现SQL注入漏洞，数据库类型: {analysis.get('database_type', 'unknown')}",
                        "severity": analysis.get("vulnerability_level", "unknown"),
                        "step": step.get("step_id")
                    })
        
        return risks
    
    def _assess_risk_severity(self, risk_description: str) -> str:
        """评估风险严重性"""
        risk_lower = risk_description.lower()
        
        if any(keyword in risk_lower for keyword in ["critical", "高危", "严重"]):
            return "critical"
        elif any(keyword in risk_lower for keyword in ["high", "medium", "中危", "中等"]):
            return "medium"
        elif any(keyword in risk_lower for keyword in ["low", "低危", "轻微"]):
            return "low"
        else:
            return "unknown"
    
    def _generate_analysis_recommendations(self, 
                                         vulnerabilities: List[Dict[str, Any]], 
                                         risks: List[Dict[str, Any]], 
                                         success_rate: float) -> List[str]:
        """生成分析建议"""
        recommendations = []
        
        # 基于漏洞生成建议
        if vulnerabilities:
            recommendations.append("发现以下安全漏洞，建议立即修复：")
            for vuln in vulnerabilities:
                vuln_type = vuln.get("type", "未知漏洞")
                severity = vuln.get("severity", "unknown")
                recommendations.append(f"  - {vuln_type} ({severity}): 参考相关安全最佳实践进行修复")
        
        # 基于风险生成建议
        if risks:
            recommendations.append("发现以下安全风险，建议加强防护：")
            for risk in risks:
                risk_type = risk.get("type", "未知风险")
                description = risk.get("description", "")
                recommendations.append(f"  - {risk_type}: {description}")
        
        # 基于成功率生成建议
        if success_rate < 0.5:
            recommendations.append("攻击成功率较低，建议：")
            recommendations.append("  - 检查目标环境是否可访问")
            recommendations.append("  - 验证工具配置是否正确")
            recommendations.append("  - 考虑使用不同的攻击策略")
        elif success_rate > 0.8:
            recommendations.append("攻击成功率较高，系统安全性需要加强：")
            recommendations.append("  - 实施更严格的安全控制")
            recommendations.append("  - 定期进行安全审计")
            recommendations.append("  - 考虑实施Web应用防火墙")
        
        # 通用建议
        if not recommendations:
            recommendations.append("未发现明显安全问题，建议：")
            recommendations.append("  - 定期进行安全测试")
            recommendations.append("  - 保持系统和应用更新")
            recommendations.append("  - 实施安全监控和告警")
        
        return recommendations
    
    def generate_report(self, 
                       execution_report: Dict[str, Any], 
                       analysis_result: AnalysisResult,
                       format: str = "html") -> Dict[str, Any]:
        """
        生成报告
        
        Args:
            execution_report: 执行报告
            analysis_result: 分析结果
            format: 报告格式 (html, markdown, json, text)
            
        Returns:
            报告内容和文件路径
        """
        self.logger.info(f"生成 {format.upper()} 格式报告")
        
        # 生成时间戳
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        challenge_title = execution_report.get("challenge", {}).get("title", "unknown").replace(" ", "_")
        
        # 生成报告内容
        if format in self.templates:
            content = self.templates[format](execution_report, analysis_result)
        else:
            self.logger.warning(f"不支持的格式: {format}，使用默认格式")
            content = self._generate_text_report(execution_report, analysis_result)
        
        # 保存报告文件
        filename = f"attack_report_{challenge_title}_{timestamp}.{format}"
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.logger.info(f"报告已保存: {filepath}")
        
        return {
            "format": format,
            "filename": filename,
            "filepath": str(filepath),
            "content": content[:1000] + "..." if len(content) > 1000 else content
        }
    
    def _generate_html_report(self, 
                             execution_report: Dict[str, Any], 
                             analysis_result: AnalysisResult) -> str:
        """生成HTML报告"""
        challenge = execution_report.get("challenge", {})
        execution_summary = execution_report.get("execution_summary", {})
        stats = execution_summary.get("statistics", {})
        
        # 构建HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CTF攻击模拟报告 - {challenge.get('title', '未知挑战')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1, h2, h3 {{ color: #333; }}
        .header {{ text-align: center; border-bottom: 2px solid #4CAF50; padding-bottom: 20px; margin-bottom: 30px; }}
        .summary {{ background: #f9f9f9; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: white; padding: 15px; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 24px; font-weight: bold; color: #4CAF50; }}
        .vulnerabilities {{ margin: 20px 0; }}
        .vuln-item {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px 15px; margin: 10px 0; }}
        .critical {{ border-left-color: #dc3545; background: #f8d7da; }}
        .medium {{ border-left-color: #ffc107; background: #fff3cd; }}
        .low {{ border-left-color: #28a745; background: #d4edda; }}
        .recommendations {{ background: #e7f3ff; padding: 20px; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .success {{ color: #28a745; }}
        .warning {{ color: #ffc107; }}
        .danger {{ color: #dc3545; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CTF攻击模拟分析报告</h1>
            <p class="timestamp">生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
        
        <div class="summary">
            <h2>挑战概览</h2>
            <p><strong>标题:</strong> {challenge.get('title', 'N/A')}</p>
            <p><strong>类别:</strong> {challenge.get('category', 'N/A')}</p>
            <p><strong>难度:</strong> {challenge.get('difficulty', 'N/A')}</p>
            <p><strong>目标URL:</strong> <a href="{challenge.get('target_url', '#')}" target="_blank">{challenge.get('target_url', 'N/A')}</a></p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">攻击成功率</div>
                <div class="stat-value">{analysis_result.success_rate:.1%}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">发现漏洞数</div>
                <div class="stat-value">{len(analysis_result.vulnerabilities)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">找到Flag数</div>
                <div class="stat-value">{len(analysis_result.flags_found)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">执行时间</div>
                <div class="stat-value">{analysis_result.execution_time:.2f}s</div>
            </div>
        </div>
        
        <h2>执行摘要</h2>
        <table>
            <tr>
                <th>指标</th>
                <th>值</th>
                <th>状态</th>
            </tr>
            <tr>
                <td>总步骤数</td>
                <td>{stats.get('total_steps', 0)}</td>
                <td>-</td>
            </tr>
            <tr>
                <td>成功步骤</td>
                <td>{stats.get('successful_steps', 0)}</td>
                <td class="success">✓</td>
            </tr>
            <tr>
                <td>失败步骤</td>
                <td>{stats.get('failed_steps', 0)}</td>
                <td class="danger">✗</td>
            </tr>
            <tr>
                <td>超时步骤</td>
                <td>{stats.get('timeout_steps', 0)}</td>
                <td class="warning">⚠</td>
            </tr>
            <tr>
                <td>总体状态</td>
                <td>{execution_summary.get('status', 'unknown')}</td>
                <td class="{'success' if execution_report.get('success') else 'danger'}">
                    {'✓ 成功' if execution_report.get('success') else '✗ 失败'}
                </td>
            </tr>
        </table>
        
        <h2>发现的Flag</h2>
        {"<ul>" + "".join(f"<li><code>{flag}</code></li>" for flag in analysis_result.flags_found) + "</ul>" if analysis_result.flags_found else "<p>未找到Flag</p>"}
        
        <h2>安全漏洞分析</h2>
        <div class="vulnerabilities">
            {self._generate_vulnerabilities_html(analysis_result.vulnerabilities)}
        </div>
        
        <h2>安全风险评估</h2>
        <div class="vulnerabilities">
            {self._generate_risks_html(analysis_result.security_risks)}
        </div>
        
        <h2>详细步骤执行</h2>
        <table>
            <tr>
                <th>步骤ID</th>
                <th>操作</th>
                <th>工具</th>
                <th>状态</th>
                <th>执行时间</th>
                <th>Flag</th>
            </tr>
            {self._generate_steps_html(execution_report.get('step_details', []))}
        </table>
        
        <h2>安全建议</h2>
        <div class="recommendations">
            {self._generate_recommendations_html(analysis_result.recommendations)}
        </div>
        
        <div class="timestamp" style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;">
            <p>报告由 CTF AI攻击模拟系统生成</p>
            <p>仅供教育和安全测试目的使用</p>
        </div>
    </div>
</body>
</html>"""
        
        return html
    
    def _generate_vulnerabilities_html(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """生成漏洞HTML"""
        if not vulnerabilities:
            return "<p>未发现安全漏洞</p>"
        
        html = ""
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "unknown").lower()
            severity_class = severity if severity in ["critical", "medium", "low"] else "unknown"
            
            html += f"""
            <div class="vuln-item {severity_class}">
                <strong>{vuln.get('type', '未知漏洞')}</strong> ({severity})<br>
                <small>步骤: {vuln.get('step', 'N/A')} | 工具: {vuln.get('tool', 'N/A')}</small><br>
                {vuln.get('description', '无描述')}
            </div>
            """
        
        return html
    
    def _generate_risks_html(self, risks: List[Dict[str, Any]]) -> str:
        """生成风险HTML"""
        if not risks:
            return "<p>未发现安全风险</p>"
        
        html = ""
        for risk in risks:
            severity = risk.get("severity", "unknown").lower()
            severity_class = severity if severity in ["critical", "medium", "low"] else "unknown"
            
            html += f"""
            <div class="vuln-item {severity_class}">
                <strong>{risk.get('type', '未知风险')}</strong> ({severity})<br>
                <small>步骤: {risk.get('step', 'N/A')}</small><br>
                {risk.get('description', '无描述')}
            </div>
            """
        
        return html
    
    def _generate_steps_html(self, step_details: List[Dict[str, Any]]) -> str:
        """生成步骤HTML"""
        html = ""
        for step in step_details:
            status = step.get("status", "unknown")
            status_html = {
                "success": '<span class="success">✓ 成功</span>',
                "failed": '<span class="danger">✗ 失败</span>',
                "timeout": '<span class="warning">⚠ 超时</span>',
                "pending": '<span>⏳ 等待</span>'
            }.get(status, f'<span>{status}</span>')
            
            flag_html = f'<code>{step.get("flag")}</code>' if step.get("flag_detected") else "-"
            
            html += f"""
            <tr>
                <td>{step.get('step_id', 'N/A')}</td>
                <td>{step.get('action', 'N/A')}</td>
                <td>{step.get('tool', '手动')}</td>
                <td>{status_html}</td>
                <td>{step.get('execution_time', 0):.2f}s</td>
                <td>{flag_html}</td>
            </tr>
            """
        
        return html
    
    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """生成建议HTML"""
        if not recommendations:
            return "<p>无建议</p>"
        
        html = "<ul>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += "</ul>"
        
        return html
    
    def _generate_markdown_report(self, 
                                 execution_report: Dict[str, Any], 
                                 analysis_result: AnalysisResult) -> str:
        """生成Markdown报告"""
        challenge = execution_report.get("challenge", {})
        execution_summary = execution_report.get("execution_summary", {})
        stats = execution_summary.get("statistics", {})
        
        md = f"""# CTF攻击模拟分析报告

## 报告信息
- **生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
- **报告格式**: Markdown
- **系统版本**: CTF AI攻击模拟系统 v1.0

## 挑战概览
- **标题**: {challenge.get('title', 'N/A')}
- **类别**: {challenge.get('category', 'N/A')}
- **难度**: {challenge.get('difficulty', 'N/A')}
- **目标URL**: {challenge.get('target_url', 'N/A')}

## 执行摘要
| 指标 | 值 | 状态 |
|------|----|------|
| 总步骤数 | {stats.get('total_steps', 0)} | - |
| 成功步骤 | {stats.get('successful_steps', 0)} | ✓ |
| 失败步骤 | {stats.get('failed_steps', 0)} | ✗ |
| 超时步骤 | {stats.get('timeout_steps', 0)} | ⚠ |
| 总体状态 | {execution_summary.get('status', 'unknown')} | {'✓ 成功' if execution_report.get('success') else '✗ 失败'} |
| 攻击成功率 | {analysis_result.success_rate:.1%} | - |
| 执行时间 | {analysis_result.execution_time:.2f}秒 | - |

## 发现的Flag
{self._generate_flag_markdown(analysis_result.flags_found)}

## 安全漏洞分析
{self._generate_vulnerabilities_markdown(analysis_result.vulnerabilities)}

## 安全风险评估
{self._generate_risks_markdown(analysis_result.security_risks)}

## 详细步骤执行
{self._generate_steps_markdown(execution_report.get('step_details', []))}

## 安全建议
{self._generate_recommendations_markdown(analysis_result.recommendations)}

---

*报告由 CTF AI攻击模拟系统生成*  
*仅供教育和安全测试目的使用*
"""
        
        return md
    
    def _generate_flag_markdown(self, flags: List[str]) -> str:
        """生成Flag Markdown"""
        if not flags:
            return "未找到Flag"
        
        md = ""
        for flag in flags:
            md += f"- `{flag}`\n"
        
        return md
    
    def _generate_vulnerabilities_markdown(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """生成漏洞Markdown"""
        if not vulnerabilities:
            return "未发现安全漏洞"
        
        md = "| 类型 | 严重性 | 步骤 | 描述 |\n|------|--------|------|------|\n"
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "unknown")
            severity_icon = {
                "critical": "🔴",
                "medium": "🟡", 
                "low": "🟢",
                "unknown": "⚪"
            }.get(severity.lower(), "⚪")
            
            md += f"| {vuln.get('type', '未知')} | {severity_icon} {severity} | {vuln.get('step', 'N/A')} | {vuln.get('description', '无描述')} |\n"
        
        return md
    
    def _generate_risks_markdown(self, risks: List[Dict[str, Any]]) -> str:
        """生成风险Markdown"""
        if not risks:
            return "未发现安全风险"
        
        md = "| 类型 | 严重性 | 步骤 | 描述 |\n|------|--------|------|------|\n"
        for risk in risks:
            severity = risk.get("severity", "unknown")
            severity_icon = {
                "critical": "🔴",
                "medium": "🟡", 
                "low": "🟢",
                "unknown": "⚪"
            }.get(severity.lower(), "⚪")
            
            md += f"| {risk.get('type', '未知')} | {severity_icon} {severity} | {risk.get('step', 'N/A')} | {risk.get('description', '无描述')} |\n"
        
        return md
    
    def _generate_steps_markdown(self, step_details: List[Dict[str, Any]]) -> str:
        """生成步骤Markdown"""
        if not step_details:
            return "无步骤执行记录"
        
        md = "| 步骤ID | 操作 | 工具 | 状态 | 执行时间 | Flag |\n|--------|------|------|------|----------|------|\n"
        for step in step_details:
            status = step.get("status", "unknown")
            status_icon = {
                "success": "✅",
                "failed": "❌",
                "timeout": "⏰",
                "pending": "⏳"
            }.get(status, "❓")
            
            flag = f"`{step.get('flag')}`" if step.get("flag_detected") else "-"
            
            md += f"| {step.get('step_id', 'N/A')} | {step.get('action', 'N/A')} | {step.get('tool', '手动')} | {status_icon} {status} | {step.get('execution_time', 0):.2f}s | {flag} |\n"
        
        return md
    
    def _generate_recommendations_markdown(self, recommendations: List[str]) -> str:
        """生成建议Markdown"""
        if not recommendations:
            return "无建议"
        
        md = ""
        for rec in recommendations:
            md += f"- {rec}\n"
        
        return md
    
    def _generate_json_report(self, 
                             execution_report: Dict[str, Any], 
                             analysis_result: AnalysisResult) -> str:
        """生成JSON报告"""
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "system": "CTF AI攻击模拟系统",
                "version": "1.0"
            },
            "challenge": execution_report.get("challenge", {}),
            "execution_summary": execution_report.get("execution_summary", {}),
            "analysis": {
                "success_rate": analysis_result.success_rate,
                "vulnerabilities_found": len(analysis_result.vulnerabilities),
                "flags_found": len(analysis_result.flags_found),
                "execution_time": analysis_result.execution_time,
                "confidence": analysis_result.confidence
            },
            "vulnerabilities": analysis_result.vulnerabilities,
            "security_risks": analysis_result.security_risks,
            "flags": analysis_result.flags_found,
            "step_details": execution_report.get("step_details", []),
            "recommendations": analysis_result.recommendations
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)
    
    def _generate_text_report(self, 
                             execution_report: Dict[str, Any], 
                             analysis_result: AnalysisResult) -> str:
        """生成文本报告"""
        challenge = execution_report.get("challenge", {})
        
        text = f"""
{'='*60}
CTF攻击模拟分析报告
{'='*60}

生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
系统版本: CTF AI攻击模拟系统 v1.0

挑战信息:
  标题: {challenge.get('title', 'N/A')}
  类别: {challenge.get('category', 'N/A')}
  难度: {challenge.get('difficulty', 'N/A')}
  目标URL: {challenge.get('target_url', 'N/A')}

执行摘要:
  攻击成功率: {analysis_result.success_rate:.1%}
  发现漏洞数: {len(analysis_result.vulnerabilities)}
  找到Flag数: {len(analysis_result.flags_found)}
  执行时间: {analysis_result.execution_time:.2f}秒

发现的Flag:
{self._generate_flag_text(analysis_result.flags_found)}

安全漏洞:
{self._generate_vulnerabilities_text(analysis_result.vulnerabilities)}

安全风险:
{self._generate_risks_text(analysis_result.security_risks)}

执行步骤:
{self._generate_steps_text(execution_report.get('step_details', []))}

安全建议:
{self._generate_recommendations_text(analysis_result.recommendations)}

{'='*60}
报告结束
{'='*60}
"""
        
        return text
    
    def _generate_flag_text(self, flags: List[str]) -> str:
        """生成Flag文本"""
        if not flags:
            return "  未找到Flag"
        
        text = ""
        for flag in flags:
            text += f"  - {flag}\n"
        
        return text
    
    def _generate_vulnerabilities_text(self, vulnerabilities: List[Dict[str, Any]]) -> str:
        """生成漏洞文本"""
        if not vulnerabilities:
            return "  未发现安全漏洞"
        
        text = ""
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "unknown")
            text += f"  - {vuln.get('type', '未知漏洞')} ({severity})\n"
            text += f"    步骤: {vuln.get('step', 'N/A')}, 工具: {vuln.get('tool', 'N/A')}\n"
            text += f"    描述: {vuln.get('description', '无描述')}\n"
        
        return text
    
    def _generate_risks_text(self, risks: List[Dict[str, Any]]) -> str:
        """生成风险文本"""
        if not risks:
            return "  未发现安全风险"
        
        text = ""
        for risk in risks:
            severity = risk.get("severity", "unknown")
            text += f"  - {risk.get('type', '未知风险')} ({severity})\n"
            text += f"    步骤: {risk.get('step', 'N/A')}\n"
            text += f"    描述: {risk.get('description', '无描述')}\n"
        
        return text
    
    def _generate_steps_text(self, step_details: List[Dict[str, Any]]) -> str:
        """生成步骤文本"""
        if not step_details:
            return "  无步骤执行记录"
        
        text = ""
        for step in step_details:
            status = step.get("status", "unknown")
            status_icon = {
                "success": "✓",
                "failed": "✗",
                "timeout": "⏰",
                "pending": "⏳"
            }.get(status, "?")
            
            flag = f", Flag: {step.get('flag')}" if step.get("flag_detected") else ""
            
            text += f"  {status_icon} 步骤 {step.get('step_id', 'N/A')}: {step.get('action', 'N/A')}\n"
            text += f"     工具: {step.get('tool', '手动')}, 状态: {status}, 时间: {step.get('execution_time', 0):.2f}s{flag}\n"
        
        return text
    
    def _generate_recommendations_text(self, recommendations: List[str]) -> str:
        """生成建议文本"""
        if not recommendations:
            return "  无建议"
        
        text = ""
        for rec in recommendations:
            text += f"  - {rec}\n"
        
        return text


# 示例使用
async def demo_report_generator():
    """演示报告生成器的使用"""
    # 创建示例执行报告
    challenge = {
        "title": "SQL注入挑战",
        "category": "web",
        "difficulty": "easy",
        "target_url": "http://testphp.vulnweb.com/artists.php?artist=1"
    }
    
    # 模拟执行报告
    execution_report = {
        "challenge": challenge,
        "execution_summary": {
            "status": "success",
            "total_time": 120.5,
            "statistics": {
                "total_steps": 2,
                "successful_steps": 2,
                "failed_steps": 0,
                "timeout_steps": 0
            }
        },
        "flags": ["flag{sql_injection_success}"],
        "step_details": [
            {
                "step_id": 1,
                "action": "端口扫描",
                "tool": "nmap_scan",
                "status": "success",
                "execution_time": 30.2,
                "flag_detected": False,
                "flag": None,
                "output": {
                    "analysis": {
                        "security_risks": ["端口 80 (http): 可能存在Web漏洞"]
                    }
                }
            },
            {
                "step_id": 2,
                "action": "SQL注入扫描",
                "tool": "sqlmap_scan",
                "status": "success",
                "execution_time": 90.3,
                "flag_detected": True,
                "flag": "flag{sql_injection_success}",
                "output": {
                    "analysis": {
                        "injection_found": True,
                        "database_type": "MySQL",
                        "vulnerability_level": "critical"
                    }
                }
            }
        ],
        "security_assessment": {
            "vulnerabilities_found": [
                {
                    "type": "SQL Injection",
                    "severity": "critical",
                    "tool": "sqlmap",
                    "step": 2,
                    "description": "发现SQL注入漏洞"
                }
            ],
            "confidence": 1.0
        },
        "success": True
    }
    
    # 创建报告生成器
    generator = ReportGenerator()
    
    # 分析执行结果
    analysis_result = generator.analyze_execution_results(execution_report)
    
    # 生成各种格式的报告
    print("生成报告中...")
    
    html_report = generator.generate_report(execution_report, analysis_result, "html")
    print(f"HTML报告已生成: {html_report['filename']}")
    
    markdown_report = generator.generate_report(execution_report, analysis_result, "markdown")
    print(f"Markdown报告已生成: {markdown_report['filename']}")
    
    json_report = generator.generate_report(execution_report, analysis_result, "json")
    print(f"JSON报告已生成: {json_report['filename']}")
    
    text_report = generator.generate_report(execution_report, analysis_result, "text")
    print(f"文本报告已生成: {text_report['filename']}")
    
    return {
        "html": html_report,
        "markdown": markdown_report,
        "json": json_report,
        "text": text_report
    }


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_report_generator())
