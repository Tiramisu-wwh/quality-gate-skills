"""
PRD 准入评审报告生成脚本
根据评审结果生成符合准入清单格式的 Excel 评审报告
"""
import xlsxwriter
from datetime import datetime
from pathlib import Path


def generate_review_report(template_path, output_path, review_results, project_info=None):
    """
    生成 PRD 准入评审报告

    Args:
        template_path: 模板 Excel 文件路径（保留参数以保持向后兼容，但实际不使用）
        output_path: 输出 Excel 文件路径
        review_results: 评审结果字典
        project_info: 项目信息字典

    Returns:
        str: 输出文件路径
    """
    # 创建新工作簿（使用 xlsxwriter）
    workbook = xlsxwriter.Workbook(output_path)
    sheet = workbook.add_worksheet('PRD准入检查清单')

    # 定义格式
    formats = {}

    # 标题格式
    formats['title'] = workbook.add_format({
        'bold': True,
        'font_size': 16,
        'font_name': '微软雅黑',
        'align': 'center',
        'valign': 'vcenter',
        'bg_color': '#4472C4',
        'font_color': 'white'
    })

    # 章节标题格式
    formats['section_title'] = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'font_name': '微软雅黑',
        'bg_color': '#E7E6E6',
        'border': 1
    })

    # 小节标题格式
    formats['subsection'] = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'font_name': '微软雅黑',
        'bg_color': '#F2F2F2',
        'border': 1
    })

    # 表头格式
    formats['header'] = workbook.add_format({
        'bold': True,
        'font_name': '微软雅黑',
        'bg_color': '#D9E1F2',
        'border': 1,
        'text_wrap': True
    })

    # 普通单元格格式
    formats['normal'] = workbook.add_format({
        'font_name': '微软雅黑',
        'border': 1,
        'valign': 'vcenter'
    })

    # 结果列格式（居中）
    formats['result'] = workbook.add_format({
        'font_name': '微软雅黑',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    # 备注列格式
    formats['note'] = workbook.add_format({
        'font_name': '微软雅黑',
        'border': 1,
        'text_wrap': True,
        'valign': 'top'
    })

    # 百分比格式
    formats['percent'] = workbook.add_format({
        'font_name': '微软雅黑',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'num_format': '0.00%'
    })

    # 结论格式
    formats['conclusion'] = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'font_name': '微软雅黑',
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#FFC000'
    })

    # 结果格式
    formats['pass'] = workbook.add_format({
        'font_name': '微软雅黑',
        'font_size': 11,
        'bold': True,
        'color': '#006100',
        'bg_color': '#C6EFCE',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    formats['fail'] = workbook.add_format({
        'font_name': '微软雅黑',
        'font_size': 11,
        'bold': True,
        'color': '#9C0006',
        'bg_color': '#FFC7CE',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    formats['not_involved'] = workbook.add_format({
        'font_name': '微软雅黑',
        'font_size': 11,
        'color': '#9C5700',
        'bg_color': '#FFEB9C',
        'border': 1,
        'align': 'center',
        'valign': 'vcenter'
    })

    # 设置列宽
    sheet.set_column('A:A', 3)
    sheet.set_column('B:B', 40)
    sheet.set_column('C:C', 12)
    sheet.set_column('D:D', 30)

    # 写入标题
    sheet.merge_range('A1:D1', 'PRD准入检查清单', formats['title'])

    # 填充基本信息
    info_data = [
        ('PRD名称', project_info.get('project_name', '') if project_info else ''),
        ('产品经理', project_info.get('product_manager', '') if project_info else ''),
        ('提交日期', datetime.now().strftime('%Y-%m-%d')),
        ('版本号', project_info.get('version', '') if project_info else ''),
        ('需求链接', project_info.get('requirement_link', '') if project_info else ''),
        ('期望发布时间', project_info.get('expected_release_date', '') if project_info else ''),
    ]

    row = 3
    for label, value in info_data:
        sheet.write(row, 0, label, formats['section_title'])
        sheet.write(row, 1, value, formats['normal'])
        row += 1

    # 写入检查清单表格（使用参考脚本的完整结构）
    row = write_checklist_tables(sheet, formats, review_results)

    # 写入评审结果区域
    row = write_review_results(sheet, row, formats, review_results)

    workbook.close()
    return output_path


def write_checklist_tables(sheet, formats, review_results):
    """写入检查清单表格"""
    # 检查项数据结构（从参考脚本复制）
    sections = [
        {
            'name': '一、文档完整性检查',
            'subsections': [
                {
                    'title': '1.1 需求背景与业务价值（可选）',
                    'items': [
                        '需求背景说明完整',
                        '业务价值明确',
                        '目标用户清晰',
                        '预期收益可衡量'
                    ]
                },
                {
                    'title': '1.2 用户角色与使用场景',
                    'items': [
                        '用户角色定义完整',
                        '使用场景描述详细',
                        '用户画像清晰',
                        '用户路径图已提供'
                    ]
                },
                {
                    'title': '1.3 功能需求描述（必要）',
                    'items': [
                        '功能列表完整',
                        '每个功能描述详细',
                        'UI交互说明清晰',
                        '界面原型/设计稿已提供'
                    ]
                },
                {
                    'title': '1.4 非功能需求',
                    'items': [
                        '性能需求已定义（响应时间、并发量、吞吐量）',
                        '安全需求已定义（数据安全、权限控制）',
                        '兼容性需求已定义（浏览器、设备、操作系统）'
                    ]
                },
                {
                    'title': '1.5 验收标准',
                    'items': [
                        '每个功能都有验收标准',
                        '验收标准可量化',
                        '验收标准可测试',
                        '验收标准与需求对应'
                    ]
                },
                {
                    'title': '1.6 依赖系统/接口',
                    'items': [
                        '依赖系统已列出',
                        '第三方服务依赖已说明'
                    ]
                },
                {
                    'title': '1.7 数据变更影响',
                    'items': [
                        '数据变更说明',
                        '数据迁移方案',
                        '数据回滚方案',
                        '历史数据处理'
                    ]
                }
            ]
        },
        {
            'name': '二、质量标准检查',
            'subsections': [
                {
                    'title': '2.1 清晰性检查',
                    'items': [
                        '需求描述无歧义',
                        '专业术语解释完整',
                        '业务术语统一',
                        '逻辑关系清晰'
                    ]
                },
                {
                    'title': '2.2 可测试性检查',
                    'items': [
                        '验收标准可测试',
                        '测试场景可识别',
                        '输入输出明确',
                        '预期结果可验证'
                    ]
                },
                {
                    'title': '2.3 完整性检查',
                    'items': [
                        '正常场景已覆盖',
                        '边界条件已定义',
                        '异常场景已覆盖',
                        '错误处理已说明'
                    ]
                },
                {
                    'title': '2.4 可实现性检查',
                    'items': [
                        '技术可行性已确认',
                        '资源需求可满足',
                        '时间评估合理',
                        '风险已识别'
                    ]
                }
            ]
        },
        {
            'name': '三、其他相关资料',
            'subsections': [
                {
                    'title': '3.1 参考资料文件检查',
                    'items': [
                        '相关的参考资料文件完整'
                    ]
                },
                {
                    'title': '3.2 模版文件检查',
                    'items': [
                        '相关的模版文件完整无误'
                    ]
                },
                {
                    'title': '3.3 业务数据检查',
                    'items': [
                        '相关的业务数据完整'
                    ]
                }
            ]
        }
    ]

    row = 11
    item_number = 1

    for section in sections:
        # 章节标题
        sheet.merge_range(row, 0, row, 3, section['name'], formats['section_title'])
        row += 1

        # 子章节和检查项
        for subsection in section['subsections']:
            # 小节标题
            sheet.merge_range(row, 0, row, 3, subsection['title'], formats['subsection'])
            row += 1

            # 表头
            sheet.write(row, 0, '序号', formats['header'])
            sheet.write(row, 1, '检查项', formats['header'])
            sheet.write(row, 2, '是否通过', formats['header'])
            sheet.write(row, 3, '备注', formats['header'])
            row += 1

            # 检查项
            for item in subsection['items']:
                # 获取评审结果
                result_data = review_results.get(str(item_number), {})
                result = result_data.get('result', '通过')
                note = result_data.get('note', '')

                # 根据结果选择格式
                result_format = formats['result']
                if result == '通过':
                    result_format = formats['pass']
                elif result == '未涉及':
                    result_format = formats['not_involved']
                elif result == '不通过':
                    result_format = formats['fail']

                sheet.write(row, 0, item_number, formats['result'])
                sheet.write(row, 1, item, formats['normal'])
                sheet.write(row, 2, result, result_format)
                sheet.write(row, 3, note, formats['note'])
                row += 1
                item_number += 1

            row += 1  # 空行

    return row


def write_review_results(sheet, row, formats, review_results):
    """写入评审结果"""
    row += 1

    # 计算通过率
    total_items = len(review_results)
    passed_items = sum(1 for r in review_results.values() if r.get('result') == '通过')
    pass_rate = (passed_items / total_items) * 100 if total_items > 0 else 0

    # 确定评审结论
    if pass_rate >= 80:
        conclusion = '通过'
        description = '所有检查项均达到要求'
    elif pass_rate >= 65:
        conclusion = '有条件通过'
        description = '接近标准但有个别遗漏，建议补充相关内容后重新评审'
    else:
        conclusion = '不通过'
        description = '存在较多问题，需完善后再评审'

    # 问题清单
    sheet.merge_range(row, 0, row, 3, '四、评审意见', formats['section_title'])
    row += 1

    sheet.merge_range(row, 0, row, 3, '4.1 问题清单', formats['subsection'])
    row += 1

    # 问题清单表头
    sheet.write(row, 0, '序号', formats['header'])
    sheet.write(row, 1, '问题描述', formats['header'])
    sheet.write(row, 2, '严重程度', formats['header'])
    sheet.write(row, 3, '建议修改方案', formats['header'])
    row += 1

    # 提取问题（只提取不通过的检查项，不包括未涉及）
    problems = []
    problem_number = 1
    for item_id, result_data in review_results.items():
        result = result_data.get('result')
        if result == '不通过' or result == '部分通过':
            severity = '高' if item_id in ['1', '9', '16', '20'] else '中'
            problems.append({
                'number': problem_number,
                'description': f"检查项{item_id}不通过",
                'severity': severity,
                'suggestion': result_data.get('note', '请补充相关内容')
            })
            problem_number += 1

    # 写入问题清单（最多5个）
    for idx, problem in enumerate(problems[:5]):
        sheet.write(row, 0, problem['number'], formats['result'])
        sheet.write(row, 1, problem['description'], formats['normal'])
        sheet.write(row, 2, problem['severity'], formats['result'])
        sheet.write(row, 3, problem['suggestion'], formats['note'])
        row += 1

    # 预留空行
    for _ in range(5 - len(problems)):
        sheet.write(row, 0, '', formats['result'])
        sheet.write(row, 1, '', formats['normal'])
        sheet.write(row, 2, '', formats['result'])
        sheet.write(row, 3, '', formats['note'])
        row += 1

    row += 1

    # 评审结论
    sheet.merge_range(row, 0, row, 3, '4.2 评审结论', formats['subsection'])
    row += 1

    # 通过率统计
    sheet.write(row, 0, '通过率', formats['normal'])
    sheet.write(row, 1, f'{pass_rate:.1f}%', formats['percent'])
    row += 1

    # 评审结果
    sheet.write(row, 0, '评审结果', formats['normal'])
    sheet.write(row, 1, conclusion, formats['conclusion'])
    row += 1

    # 说明
    sheet.write(row, 0, '说明', formats['normal'])
    sheet.merge_range(row, 1, row, 3, description, formats['note'])

    return row


if __name__ == '__main__':
    # 测试代码
    template_path = str(Path(__file__).resolve().parents[1] / 'assets' / 'PRD准入检查清单模板.xlsx')
    output_path = '/tmp/test_review_report.xlsx'

    # 模拟评审结果（完整43项）
    test_results = {
        '1': {'result': '通过', 'note': ''},
        '2': {'result': '通过', 'note': ''},
        '3': {'result': '通过', 'note': ''},
        '4': {'result': '通过', 'note': ''},
        '5': {'result': '通过', 'note': ''},
        '6': {'result': '通过', 'note': ''},
        '7': {'result': '通过', 'note': ''},
        '8': {'result': '通过', 'note': ''},
        '9': {'result': '不通过', 'note': '缺少业务价值说明'},
        '10': {'result': '不通过', 'note': ''},
        '11': {'result': '通过', 'note': ''},
        '12': {'result': '通过', 'note': ''},
        '13': {'result': '通过', 'note': ''},
        '14': {'result': '通过', 'note': ''},
        '15': {'result': '通过', 'note': ''},
        '16': {'result': '通过', 'note': ''},
        '17': {'result': '通过', 'note': ''},
        '18': {'result': '通过', 'note': ''},
        '19': {'result': '通过', 'note': ''},
        '20': {'result': '通过', 'note': ''},
        '21': {'result': '通过', 'note': ''},
        '22': {'result': '未涉及', 'note': '无历史数据'},
        '23': {'result': '通过', 'note': ''},
        '24': {'result': '通过', 'note': ''},
        '25': {'result': '通过', 'note': ''},
        '26': {'result': '通过', 'note': ''},
        '27': {'result': '通过', 'note': ''},
        '28': {'result': '通过', 'note': ''},
        '29': {'result': '通过', 'note': ''},
        '30': {'result': '通过', 'note': ''},
        '31': {'result': '通过', 'note': ''},
        '32': {'result': '通过', 'note': ''},
        '33': {'result': '通过', 'note': ''},
        '34': {'result': '通过', 'note': ''},
        '35': {'result': '通过', 'note': ''},
        '36': {'result': '通过', 'note': ''},
        '37': {'result': '通过', 'note': ''},
        '38': {'result': '通过', 'note': ''},
        '39': {'result': '通过', 'note': ''},
        '40': {'result': '通过', 'note': ''},
        '41': {'result': '通过', 'note': ''},
        '42': {'result': '通过', 'note': ''},
        '43': {'result': '通过', 'note': ''},
    }

    # 模拟项目信息
    test_project_info = {
        'project_name': '测试项目',
        'product_manager': '张三',
        'version': 'v1.0',
        'requirement_link': 'http://example.com',
        'expected_release_date': '2026-03-20',
    }

    generate_review_report(template_path, output_path, test_results, test_project_info)
    print(f"评审报告已生成: {output_path}")
