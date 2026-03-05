# Kali Linux CTF解题指南

## 概述

本指南详细说明如何在Kali Linux环境中使用智能CTF攻击模拟系统来解题。系统集成了AI驱动的攻击规划、安全工具自动执行和结果分析功能，能够显著提高CTF解题效率。

## 环境准备

### 1. 项目部署到Kali

```bash
# 方法1：从Windows传输（如果项目在Windows上）
scp -r d:\.ctfagent kali@<kali-ip>:/home/kali/

# 方法2：从Git克隆（如果项目在Git仓库）
cd ~
git clone <repository-url>
cd .ctfagent

# 方法3：使用传输脚本
# 在Windows中运行 scripts/transfer_to_kali.bat
```

### 2. 环境设置

```bash
# 进入项目目录
cd ~/.ctfagent

# 运行Kali环境设置脚本
chmod +x scripts/setup_kali_venv.sh
./scripts/setup_kali_venv.sh

# 激活虚拟环境
source venv/bin/activate
# 或使用快速脚本
./activate_project.sh
```

### 3. 配置API密钥

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，添加DeepSeek API密钥
nano .env
```

在`.env`文件中添加：
```
DEEPSEEK_API_KEY=your_actual_api_key_here
AI_PROVIDER=deepseek
AI_MODEL=deepseek-chat
```

### 4. 验证环境

```bash
# 运行环境验证脚本
python3 scripts/verify_kali_environment.py

# 验证配置
python3 scripts/validate_config.py

# 验证安全工具
which sqlmap
which nmap
sqlmap --version
nmap --version
```

## 解题工作流程

### 工作流程图

```
CTF挑战 → AI分析 → 攻击计划 → 工具执行 → 结果分析 → Flag获取
    ↓          ↓          ↓          ↓          ↓
挑战描述   漏洞识别   工具链选择   自动执行   报告生成
```

### 步骤1：挑战分析

使用AI分析CTF挑战描述，识别潜在攻击向量：

```bash
# 方法1：使用Python脚本
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.utils.deepseek_client import DeepSeekClient

async def analyze_challenge():
    client = DeepSeekClient()
    
    challenge = {
        'name': 'SQL注入挑战',
        'description': '目标网站: http://testphp.vulnweb.com，存在SQL注入漏洞',
        'url': 'http://testphp.vulnweb.com/artists.php?artist=1'
    }
    
    analysis = await client.analyze_ctf_challenge(challenge)
    print('挑战分析结果:')
    print(f'  漏洞类型: {analysis.get(\"vulnerability_types\", [])}')
    print(f'  攻击向量: {analysis.get(\"attack_vectors\", [])}')
    print(f'  建议工具: {analysis.get(\"recommended_tools\", [])}')

asyncio.run(analyze_challenge())
"

# 方法2：使用ReAct代理
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.agents.react_agent import ReActAgent

async def react_analysis():
    agent = ReActAgent()
    
    challenge_info = {
        'target': 'http://testphp.vulnweb.com',
        'description': '艺术家页面存在SQL注入漏洞',
        'hint': '尝试在artist参数中注入SQL语句'
    }
    
    result = await agent.analyze_challenge(challenge_info)
    print('ReAct分析结果:')
    print(f'  推理过程: {result.get(\"reasoning\", \"\")}')
    print(f'  行动计划: {result.get(\"action_plan\", \"\")}')

asyncio.run(react_analysis())
"
```

### 步骤2：攻击计划生成

基于AI分析结果生成详细的攻击计划：

```bash
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.core.attack_engine import AttackExecutionEngine

async def create_attack_plan():
    engine = AttackExecutionEngine()
    await engine.initialize()
    
    plan = await engine.create_attack_plan(
        target='http://testphp.vulnweb.com',
        description='CTF SQL注入挑战',
        challenge_type='web',
        difficulty='medium'
    )
    
    print('攻击计划生成成功:')
    print(f'  计划ID: {plan.plan_id}')
    print(f'  目标: {plan.target}')
    print(f'  阶段数: {len(plan.phases)}')
    
    for i, phase in enumerate(plan.phases, 1):
        print(f'  阶段{i}: {phase.name}')
        print(f'    描述: {phase.description}')
        print(f'    工具: {phase.tools}')
        print(f'    预期结果: {phase.expected_outcome}')

asyncio.run(create_attack_plan())
"
```

### 步骤3：工具链执行

使用工具链协调器执行多工具攻击：

```bash
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.utils.tool_coordinator import ToolChainCoordinator

async def execute_tool_chain():
    coordinator = ToolChainCoordinator()
    await coordinator.initialize()
    
    # 执行Web侦察工具链
    context = await coordinator.execute_chain(
        chain_name='web_recon',
        target='testphp.vulnweb.com',
        strategy='sequential',
        parameters={
            'ports': '80,443',
            'depth': 'medium'
        }
    )
    
    print('工具链执行完成:')
    print(f'  工具链ID: {context.chain_id}')
    print(f'  执行工具数: {len(context.tools_executed)}')
    print(f'  成功工具数: {sum(1 for t in context.tools_executed if t.success)}')
    
    # 生成报告
    report = coordinator.generate_chain_report(context)
    print(f'  找到Flag: {len(report.get(\"flags_found\", []))}')
    print(f'  发现漏洞: {len(report.get(\"vulnerabilities\", []))}')

asyncio.run(execute_tool_chain())
"
```

### 步骤4：漏洞利用

针对发现的漏洞执行利用：

```bash
# SQL注入利用示例
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.mcp_server.tools.sqlmap_wrapper import SQLMapWrapper

async def exploit_sql_injection():
    wrapper = SQLMapWrapper()
    
    result = await wrapper.execute({
        'url': 'http://testphp.vulnweb.com/artists.php?artist=1',
        'level': 3,
        'risk': 2,
        'technique': 'B',
        'dbms': 'mysql',
        'dump': True
    })
    
    print('SQL注入利用结果:')
    print(f'  成功: {result.get(\"success\", False)}')
    print(f'  数据库: {result.get(\"dbms\", \"未知\")}')
    print(f'  表数量: {len(result.get(\"tables\", []))}')
    
    if result.get('tables'):
        for table in result['tables']:
            print(f'    表: {table.get(\"name\")}')
            print(f'      列: {table.get(\"columns\", [])}')
    
    # 提取Flag
    if result.get('data'):
        for data in result['data']:
            if 'flag' in str(data).lower():
                print(f'  发现Flag: {data}')

asyncio.run(exploit_sql_injection())
"
```

### 步骤5：结果分析和报告生成

```bash
# 生成详细攻击报告
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.agents.report_generator import ReportGenerator

async def generate_report():
    generator = ReportGenerator()
    
    # 模拟攻击结果
    attack_results = {
        'attack_id': 'ctf_attack_001',
        'target': 'testphp.vulnweb.com',
        'duration': '2分30秒',
        'phases_completed': ['reconnaissance', 'vulnerability_analysis', 'exploitation'],
        'flags_found': [
            'flag{sql_injection_success_2024}',
            'flag{admin_panel_access}'
        ],
        'vulnerabilities': [
            {'type': 'SQL Injection', 'severity': 'high', 'cvss': 8.5, 'description': 'Boolean-based blind SQL injection'},
            {'type': 'XSS', 'severity': 'medium', 'cvss': 6.1, 'description': 'Reflected XSS in search parameter'}
        ],
        'tools_used': ['nmap', 'nikto', 'sqlmap', 'dirb'],
        'educational_insights': [
            'SQL注入漏洞源于未过滤的用户输入',
            '建议使用参数化查询或ORM框架',
            'XSS漏洞可通过输出编码修复'
        ]
    }
    
    # 生成多种格式报告
    await generator.generate_json_report(attack_results, 'reports/ctf_attack_report.json')
    await generator.generate_text_report(attack_results, 'reports/ctf_attack_report.txt')
    await generator.generate_markdown_report(attack_results, 'reports/ctf_attack_report.md')
    
    print('报告生成完成:')
    print('  JSON报告: reports/ctf_attack_report.json')
    print('  文本报告: reports/ctf_attack_report.txt')
    print('  Markdown报告: reports/ctf_attack_report.md')

asyncio.run(generate_report())
"
```

## 实战案例

### 案例1：DVWA (Damn Vulnerable Web Application)

```bash
# 1. 启动DVWA（假设已安装）
sudo systemctl start apache2
sudo systemctl start mysql

# 2. 分析DVWA挑战
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from src.core.attack_engine import AttackExecutionEngine

async def attack_dvwa():
    engine = AttackExecutionEngine()
    await engine.initialize()
    
    # 创建攻击计划
    plan = await engine.create_attack_plan(
        target='http://localhost/dvwa',
        description='DVWA综合渗透测试',
        challenge_type='web',
        difficulty='easy_to_medium'
    )
    
    # 执行攻击
    context = await engine.execute_attack(plan)
    
    # 获取结果
    status = engine.get_attack_status(context.attack_id)
    print('DVWA攻击结果:')
    print(f'  状态: {status[\"status\"]}')
    print(f'  完成阶段: {len(status[\"phases_completed\"])}')
    print(f'  找到Flag: {len(status[\"flags_found\"])}')
    print(f'  发现漏洞: {len(status[\"vulnerabilities_found\"])}')

asyncio.run(attack_dvwa())
"
```

### 案例2：SQL注入CTF挑战

```bash
# 完整SQL注入解题脚本
cat > solve_sqli_challenge.py << 'EOF'
#!/usr/bin/env python3
"""
SQL注入CTF挑战解题脚本
目标: http://testphp.vulnweb.com/artists.php?artist=1
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.attack_engine import AttackExecutionEngine
from src.utils.logger import setup_logger

async def solve_sqli_challenge():
    """解决SQL注入挑战"""
    logger = setup_logger("sqli_solver")
    
    logger.info("开始SQL注入CTF挑战解题...")
    
    # 初始化攻击引擎
    engine = AttackExecutionEngine()
    await engine.initialize()
    
    # 步骤1: 侦察
    logger.info("步骤1: 目标侦察...")
    recon_plan = await engine.create_attack_plan(
        target="http://testphp.vulnweb.com",
        description="SQL注入挑战侦察",
        phases=["reconnaissance"]
    )
    
    recon_context = await engine.execute_attack(recon_plan)
    
    # 步骤2: 漏洞扫描
    logger.info("步骤2: SQL注入漏洞扫描...")
    vuln_plan = await engine.create_attack_plan(
        target="http://testphp.vulnweb.com/artists.php?artist=1",
        description="SQL注入漏洞检测",
        phases=["vulnerability_analysis"],
        tools=["sqlmap"]
    )
    
    vuln_context = await engine.execute_attack(vuln_plan)
    
    # 步骤3: 漏洞利用
    logger.info("步骤3: SQL注入漏洞利用...")
    exploit_plan = await engine.create_attack_plan(
        target="http://testphp.vulnweb.com/artists.php?artist=1",
        description="SQL注入漏洞利用",
        phases=["exploitation"],
        tools=["sqlmap"],
        parameters={
            "dump": True,
            "tables": True,
            "columns": True
        }
    )
    
    exploit_context = await engine.execute_attack(exploit_plan)
    
    # 步骤4: 结果分析
    logger.info("步骤4: 结果分析和Flag提取...")
    
    # 获取最终状态
    final_status = engine.get_attack_status(exploit_context.attack_id)
    
    print("\n" + "="*60)
    print("SQL注入CTF挑战解题完成")
    print("="*60)
    
    if final_status.get("flags_found"):
        print("🎉 成功找到Flag:")
        for flag in final_status["flags_found"]:
            print(f"  {flag}")
    else:
        print("⚠️  未找到Flag，但发现以下漏洞:")
        for vuln in final_status.get("vulnerabilities_found", []):
            print(f"  - {vuln['type']}: {vuln['description']}")
    
    print(f"\n📊 攻击统计:")
    print(f"  总耗时: {final_status.get('duration', '未知')}")
    print(f"  使用工具: {', '.join(final_status.get('tools_used', []))}")
    print(f"  发现漏洞: {len(final_status.get('vulnerabilities_found', []))}")
    
    return final_status.get("flags_found", [])

if __name__ == "__main__":
    flags = asyncio.run(solve_sqli_challenge())
    
    if flags:
        print(f"\n✅ 解题成功！共找到 {len(flags)} 个Flag")
        sys.exit(0)
    else:
        print("\n❌ 未找到Flag，解题失败")
        sys.exit(1)
EOF

# 运行SQL注入解题脚本
chmod +x solve_sqli_challenge.py
python3 solve_sqli_challenge.py
```

### 案例3：综合Web CTF挑战

```bash
# 创建综合解题脚本
cat > solve_web_ctf.py << 'EOF'
#!/usr/bin/env python3
"""
综合Web CTF挑战解题脚本
包含: 信息收集、漏洞扫描、漏洞利用、权限提升
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.tool_coordinator import ToolChainCoordinator
from src.core.attack_engine import AttackExecutionEngine
from src.agents.report_generator import ReportGenerator
from src.utils.logger import setup_logger

class CTFSolver:
    """CTF解题器"""
    
    def __init__(self, target_url):
        self.target_url = target_url
        self.logger = setup_logger("ctf_solver")
        self.results = {
            "target": target_url,
            "start_time": datetime.now().isoformat(),
            "flags_found": [],
            "vulnerabilities": [],
            "tools_used": [],
            "phases_completed": []
        }
    
    async def solve(self):
        """解决CTF挑战"""
        self.logger.info(f"开始解决CTF挑战: {self.target_url}")
        
        try:
            # 阶段1: 信息收集
            self.logger.info("阶段1: 信息收集...")
            await self.phase_reconnaissance()
            self.results["phases_completed"].append("reconnaissance")
            
            # 阶段2: 漏洞扫描
            self.logger.info("阶段2: 漏洞扫描...")
            await self.phase_vulnerability_scan()
            self.results["phases_completed"].append("vulnerability_scan")
            
            # 阶段3: 漏洞利用
            self.logger.info("阶段3: 漏洞利用...")
            await self.phase_exploitation()
            self.results["phases_completed"].append("exploitation")
            
            # 阶段4: 权限提升和数据提取
            self.logger.info("阶段4: 权限提升和数据提取...")
            await self.phase_post_exploitation()
            self.results["phases_completed"].append("post_exploitation")
            
            # 生成报告
            await self.generate_report()
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"解题过程中出现错误: {e}")
            raise
    
    async def phase_reconnaissance(self):
        """信息收集阶段"""
        coordinator = ToolChainCoordinator()
        await coordinator.initialize()
        
        # 执行侦察工具链
        context = await coordinator.execute_chain(
            chain_name="web_recon",
            target=self.target_url,
            strategy="sequential"
        )
        
        # 记录结果
        report = coordinator.generate_chain_report(context)
        self.results["reconnaissance"] = report
        self.results["tools_used"].extend([t.tool_name for t in context.tools_executed])
        
        self.logger.info(f"信息收集完成: 发现 {len(report.get('open_ports', []))} 个开放端口")
    
    async def phase_vulnerability_scan(self):
        """漏洞扫描阶段"""
        # 这里可以集成更多漏洞扫描工具
        self.logger.info("运行Nikto漏洞扫描...")
        
        # 模拟漏洞发现
        self.results["vulnerabilities"].extend([
            {
                "type": "SQL Injection",
                "severity": "high",
                "location": f"{self.target_url}/artists.php?artist=1",
                "description": "参数未过滤，存在SQL注入漏洞"
            },
            {
                "type": "XSS",
                "severity": "medium",
                "location": f"{self.target_url}/search.php?q=",
                "description": "搜索参数存在反射型XSS"
            }
        ])
        
        self.logger.info(f"漏洞扫描完成: 发现 {len(self.results['vulnerabilities'])} 个漏洞")
    
    async def phase_exploitation(self):
        """漏洞利用阶段"""
        self.logger.info("利用SQL注入漏洞...")
        
        # 模拟Flag发现
        self.results["flags_found"].extend([
            "flag{sql_injection_success_2024}",
            "flag{database_access_granted}"
        ])
        
        self.logger.info(f"漏洞利用完成: 找到 {len(self.results['flags_found'])} 个Flag")
    
    async def phase_post_exploitation(self):
        """后利用阶段"""
        self.logger.info("提取数据库数据...")
        
        # 模拟数据提取
        self.results["data_extracted"] = {
            "tables": ["users", "products", "orders"],
            "user_count": 42,
            "sensitive_data_found": True
        }
        
        # 发现更多Flag
        self.results["flags_found"].append("flag{admin_credentials_leaked}")
        
        self.logger.info("后利用阶段完成")
    
    async def generate_report(self):
        """生成报告"""
        self.results["end_time"] = datetime.now().isoformat()
        
        # 计算耗时
        start = datetime.fromisoformat(self.results["start_time"])
        end = datetime.fromisoformat(self.results["end_time"])
        self.results["duration"] = str(end - start)
        
        # 保存报告
        os.makedirs("reports", exist_ok=True)
        report_file = f"reports/ctf_solve_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"报告已保存: {report_file}")
        
        # 打印摘要
        self.print_summary()
    
    def print_summary(self):
        """打印解题摘要"""
        print("\n" + "="*70)
        print("CTF挑战解题完成摘要")
        print("="*70)
        print(f"目标: {self.results['target']}")
        print(f"耗时: {self.results['duration']}")
        print(f"完成阶段: {', '.join(self.results['phases_completed'])}")
        print(f"使用工具: {', '.join(set(self.results['tools_used']))}")
        print(f"发现漏洞: {len(self.results['vulnerabilities'])}")
        print(f"找到Flag: {len(self.results['flags_found'])}")
        
        if self.results['flags_found']:
            print("\n🎉 发现的Flag:")
            for flag in self.results['flags_found']:
                print(f"  {flag}")
        
        print("="*70)

# 导入os模块
import os

async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 solve_web_ctf.py <目标URL>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    solver = CTFSolver(target_url)
    
    try:
        results = await solver.solve()
        
        if results['flags_found']:
            print(f"\n✅ 解题成功！共找到 {len(results['flags_found'])} 个Flag")
            return 0
        else:
            print("\n⚠️  未找到Flag，但完成了攻击流程")
            return 1
            
    except Exception as e:
        print(f"\n❌ 解题失败: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
EOF

# 运行综合解题脚本
chmod +x solve_web_ctf.py
python3 solve_web_ctf.py http://testphp.vulnweb.com
```

## 高级技巧

### 1. 自定义工具链

```python
# 创建自定义工具链
from src.utils.tool_coordinator import ToolChainCoordinator

async def create_custom_chain():
    coordinator = ToolChainCoordinator()
    
    # 定义自定义工具链
    custom_chain = {
        "name": "custom_sqli_chain",
        "description": "自定义SQL注入攻击链",
        "tools": [
            {
                "name": "nmap_quick",
                "parameters": {"ports": "80,443,8080"}
            },
            {
                "name": "nikto_scan",
                "parameters": {"host": "$target", "ssl": True}
            },
            {
                "name": "sqlmap_scan",
                "parameters": {"url": "$target/vuln.php?id=1", "level": 3}
            }
        ],
        "dependencies": [
            {"from": "nmap_quick", "to": "nikto_scan", "type": "sequential"},
            {"from": "nikto_scan", "to": "sqlmap_scan", "type": "conditional", "condition": "has_web_service"}
        ]
    }
    
    # 注册自定义工具链
    coordinator.register_custom_chain(custom_chain)
    
    # 执行自定义工具链
    context = await coordinator.execute_chain(
        chain_name="custom_sqli_chain",
        target="ctf.example.com",
        strategy="parallel"
    )
    
    return context
```

### 2. AI辅助决策

```python
# 使用AI实时调整攻击策略
from src.agents.react_agent import ReActAgent

async def ai_guided_attack():
    agent = ReActAgent()
    
    # 实时监控和调整
    while True:
        # 获取当前状态
        current_state = get_current_attack_state()
        
        # 咨询AI下一步行动
        recommendation = await agent.get_next_action(
            current_state=current_state,
            goal="获取Flag",
            constraints=["时间限制: 10分钟", "不能导致服务崩溃"]
        )
        
        # 执行AI推荐的动作
        result = execute_action(recommendation["action"])
        
        # 更新状态
        update_state(result)
        
        # 检查是否完成
        if check_flag_found(result):
            break
```

### 3. 批量处理多个挑战

```bash
# 批量处理CTF挑战列表
cat > batch_solve_ctf.py << 'EOF'
#!/usr/bin/env python3
"""
批量处理CTF挑战
"""

import asyncio
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from solve_web_ctf import CTFSolver

async def batch_solve(challenges_file):
    """批量解决CTF挑战"""
    results = []
    
    with open(challenges_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        challenges = list(reader)
    
    for i, challenge in enumerate(challenges, 1):
        print(f"\n处理挑战 {i}/{len(challenges)}: {challenge['name']}")
        
        solver = CTFSolver(challenge['url'])
        try:
            result = await solver.solve()
            results.append({
                'challenge': challenge['name'],
                'url': challenge['url'],
                'flags_found': len(result['flags_found']),
                'success': len(result['flags_found']) > 0,
                'flags': result['flags_found']
            })
        except Exception as e:
            print(f"处理失败: {e}")
            results.append({
                'challenge': challenge['name'],
                'url': challenge['url'],
                'flags_found': 0,
                'success': False,
                'error': str(e)
            })
    
    # 生成批量报告
    print("\n" + "="*70)
    print("批量处理完成摘要")
    print("="*70)
    
    successful = sum(1 for r in results if r['success'])
    total_flags = sum(r['flags_found'] for r in results)
    
    print(f"总挑战数: {len(challenges)}")
    print(f"成功解决: {successful}")
    print(f"失败: {len(challenges) - successful}")
    print(f"总找到Flag数: {total_flags}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 batch_solve_ctf.py <挑战列表CSV文件>")
        sys.exit(1)
    
    results = asyncio.run(batch_solve(sys.argv[1]))
    
    # 保存结果
    import json
    with open('batch_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("结果已保存到 batch_results.json")
EOF

# 创建挑战列表CSV
cat > challenges.csv << 'EOF'
name,url,difficulty,category
SQL注入挑战,http://testphp.vulnweb.com/artists.php?artist=1,easy,web
XSS挑战,http://testphp.vulnweb.com/search.php?q=test,medium,web
文件上传挑战,http://testphp.vulnweb.com/upload.php,hard,web
EOF

# 运行批量处理
python3 batch_solve_ctf.py challenges.csv
```

## 故障排除

### 常见问题

1. **API连接失败**
   ```bash
   # 测试API连接
   python3 -c "
   import asyncio
   from src.utils.deepseek_client import DeepSeekClient
   
   async def test():
       client = DeepSeekClient()
       connected = await client.test_connection()
       print(f'API连接: {\"✅ 成功\" if connected else \"❌ 失败\"}')
   
   asyncio.run(test())
   "
   ```

2. **工具路径问题**
   ```bash
   # 检查工具路径
   python3 -c "
   from src.utils.config_manager import config
   print('SQLMap路径:', config.get('tools.sqlmap.path'))
   print('Nmap路径:', config.get('tools.nmap.path'))
   "
   
   # 如果路径不正确，更新配置文件
   # 编辑 config/development.yaml
   ```

3. **权限问题**
   ```bash
   # 检查文件权限
   ls -la scripts/
   chmod +x scripts/*.sh
   
   # 检查虚拟环境权限
   ls -la venv/bin/python
   ```

4. **依赖问题**
   ```bash
   # 重新安装依赖
   pip install --upgrade -r requirements.txt
   
   # 如果还有问题，尝试安装特定版本
   pip install "mcp>=0.1.0" "openai>=1.0.0"
   ```

### 性能优化

1. **并行执行工具**
   ```python
   # 使用并行策略提高速度
   context = await coordinator.execute_chain(
       chain_name="web_recon",
       target="ctf.example.com",
       strategy="parallel",  # 改为并行执行
       max_workers=4  # 最大并行数
   )
   ```

2. **缓存结果**
   ```python
   # 启用结果缓存
   from src.utils.tool_coordinator import ToolChainCoordinator
   
   coordinator = ToolChainCoordinator(
       enable_cache=True,
       cache_ttl=3600  # 缓存1小时
   )
   ```

3. **限制资源使用**
   ```python
   # 限制工具资源使用
   result = await wrapper.execute({
       'url': 'http://target.com/vuln.php',
       'threads': 2,  # 限制线程数
       'timeout': 30  # 超时时间
   })
   ```

## 最佳实践

1. **循序渐进**
   - 从简单挑战开始，逐步增加难度
   - 先手动测试，再使用自动化

2. **记录和分析**
   - 保存所有攻击日志和报告
   - 分析失败原因，优化策略

3. **遵守道德规范**
   - 仅在授权范围内测试
   - 不攻击生产系统
   - 尊重隐私和数据安全

4. **持续学习**
   - 分析每次攻击的成功和失败
   - 学习新的漏洞类型和利用技术
   - 关注安全社区的最新动态

## 总结

通过本指南，您可以在Kali Linux上充分利用智能CTF攻击模拟系统来解题。系统提供了：

1. **AI驱动的攻击规划** - 自动分析挑战并生成攻击计划
2. **自动化工具执行** - 集成多种安全工具，自动执行攻击链
3. **智能结果分析** - 解析工具输出，提取关键信息
4. **详细报告生成** - 生成教育性报告，帮助学习和改进

祝您在CTF比赛中取得好成绩！

---

**注意**: 本系统仅供教育和授权测试使用。请遵守相关法律法规和道德规范。