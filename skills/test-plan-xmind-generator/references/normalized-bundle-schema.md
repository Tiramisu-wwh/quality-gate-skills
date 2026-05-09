# 标准化 Bundle 结构

在运行生成脚本之前，先整理出一份精简 JSON。

```json
{
  "project_name": "string",
  "overview": "string",
  "scope": {
    "in_scope": ["string"],
    "out_of_scope": ["string"]
  },
  "test_strategy": ["string"],
  "key_risks": ["string"],
  "environment": {
    "test_env": "string",
    "dependencies": ["string"]
  },
  "modules": [
    {
      "name": "string",
      "requirements": [
        {
          "title": "string",
          "test_points": ["string"],
          "notes": ["string"],
          "exceptions": ["string"],
          "dependencies": ["string"]
        }
      ]
    }
  ],
  "cross_cutting": {
    "interfaces": ["string"],
    "exceptions": ["string"],
    "risks": ["string"]
  },
  "assumptions": ["string"]
}
```

## 说明

- bundle 结构保持轻量和宽松。
- 某些部分暂时未知时，用空数组表示，不要凭空补数据。
- XMind 优先使用“模块 -> 需求 -> 说明节点”的结构，因此 `requirements` 推荐使用对象数组，而不是简单字符串数组。
- 需求对象中的 `notes` 用于承载主流程、接口口径、实现注意项等补充说明。
- 生成脚本允许部分字段缺失，并会在缺失分支中补上 `未提供`。
- bundle 中的文本值默认写成通用中文测试表达，不把项目内部术语当成默认语言。
- 只有在确实影响测试判定或追溯时，才在值中保留项目专有字段名、接口名、表名或系统名。
