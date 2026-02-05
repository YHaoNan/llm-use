---
name: tdd-dyncode
description: 当你在编写dyncode脚本时，比如在实现安全管理指标，动态风险指标时，且用户明确要求使用TDD驱动开发，你应该使用该skill
---



你应该只对dyncode脚本进行单元测试，不用进行集成测试、web端测试等。

## 用户变量
- mvn仓库位置：required
- mvn settings文件位置：required

- 你可以先探测常见的编辑器配置文件路径，以获取mvn仓库位置和settings文件位置。
- 如果在该skill文件中描述了路径，请直接使用
- 如果获取不到，请你询问用户
- 只有变量确定后，才可以继续向下推进

## TDD 工作流程
1.  **先写测试**：先思考并为脚本编写测试用例。对于每一个测试用例，你应该给足中文注释来描述测试的场景和预期结果。用户稍后会review你的注释。
2.  **最小化实现**：编写最简单的代码使测试通过
3.  **重构**：在测试保持绿色的前提下优化代码结构


## 1. 单元测试 (JUnit 5 + Mockito + dyncode testkit)
- **目的**：隔离测试服务层或组件的业务逻辑。
- **最佳实践**：
  - 遵循 **Arrange-Act-Assert** (准备-执行-断言) 模式。
  - 不要使用`@InjectScript`，仅使用`@InjectScriptKey`
  - 注意import语句
  - 在tsingyun-app-risk-implement/src/main/test/java/scripts/目录下实现测试
  - 测试框架在tsingyun-app-risk-implement/src/main/test/java/net/tsingyun/app/risk/common/dyncode/testkit/中

```java
package scripts.metrics.barrier;

import net.tsingyun.app.risk.common.dyncode.DynCodeExecuteEngine;
import net.tsingyun.app.risk.common.dyncode.testkit.*;
import net.tsingyun.app.risk.domain.index.RiskSafetyMetricsBarrierLevels;
import net.tsingyun.app.risk.domain.list.RiskList;
import net.tsingyun.app.risk.domain.list.RiskListNodeBowtie;
import net.tsingyun.app.risk.service.index.RiskSafetyMetricsBarrierLevelsService;
import net.tsingyun.app.risk.service.list.RiskListNodeBowtieService;
import net.tsingyun.app.risk.service.list.RiskListService;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentMatchers;
import org.mockito.Mockito;

import java.util.Arrays;


@DynCodeTest(script = "metrics/barrier/BarrierWarningRedCountList.groovy")
class BarrierWarningRedCountListTests {

    @MockBean
    RiskSafetyMetricsBarrierLevelsService barrierLevelsService;

    @MockBean
    RiskListNodeBowtieService riskListNodeBowtieService;

    @MockBean
    RiskListService riskListService;

    @InjectEngine
    DynCodeExecuteEngine engine;

    @InjectScriptKey
    String scriptKey;

    @Test
    void testRun_ReturnsExpectedDetailList() {
        Mockito.when(barrierLevelsService.listBy(ArgumentMatchers.any())).thenReturn(Arrays.asList(
                new RiskSafetyMetricsBarrierLevels(0L, 10L, 4),
                new RiskSafetyMetricsBarrierLevels(0L, 11L, 3)
        ));
        Mockito.when(riskListNodeBowtieService.listBy(ArgumentMatchers.any())).thenReturn(Arrays.asList(
                RiskListNodeBowtie.builder().id(10L).riskId(100L).name("屏障A").build()
        ));
        Mockito.when(riskListService.listBy(ArgumentMatchers.any())).thenReturn(Arrays.asList(
                RiskList.builder().id(100L).riskSceneName("场景1").build()
        ));

        Object result = engine.invoke(scriptKey, "run", Arrays.asList(0L));

        String json = String.valueOf(result);
        Assertions.assertTrue(json.contains("屏障A"));
        Assertions.assertTrue(json.contains("场景1"));
        Assertions.assertTrue(json.contains("红色"));

        Mockito.verify(barrierLevelsService).listBy(ArgumentMatchers.any());
        Mockito.verify(riskListNodeBowtieService).listBy(ArgumentMatchers.any());
        Mockito.verify(riskListService).listBy(ArgumentMatchers.any());
    }
}
```


## 核心原则
- **快速**：测试套件应在几分钟内完成，鼓励频繁执行。
- **隔离**：一个测试的失败不应导致其他测试失败。
- **确定性**：每次运行结果应相同，不依赖外部状态或随机性。
- **测试行为，而非实现细节**：关注“做什么”而不是“怎么做”，使重构更安全。
