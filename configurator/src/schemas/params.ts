/**
 * 参数类型定义 —— 可扩展的参数 Schema
 *
 * 新增参数只需添加条目到 JOINT_SCHEMAS，组件自动渲染。
 * 新增参数类型只需扩展 ParamType 并在 JointCard 中加对应分支。
 */

// ---- 基础类型 ----

/** 参数控件类型（可扩展：'dropdown' | 'input' | ...） */
export type ParamType = 'slider' | 'toggle';

/** 单个参数的描述 */
export interface ParamDef {
  /** 协议中使用的 key，如 "kp"、"torque_limit" */
  key: string;
  /** UI 显示名称 */
  label: string;
  /** 控件类型 */
  type: ParamType;
  /** 滑块最小值 */
  min?: number;
  /** 滑块最大值 */
  max?: number;
  /** 步进 */
  step?: number;
  /** 单位（可选），如 "Nm"、"rad/s" */
  unit?: string;
  /** 默认值 */
  defaultValue: number;
}

/** 一个关节的完整参数 Schema */
export interface JointSchema {
  jointName: string;
  params: ParamDef[];
}

/**
 * 5 关节机械臂参数定义
 *
 * 关节名来自 URDF: J1, J2, J3, J4, J5
 * (J_END_EFF 是 MoveIt 虚拟末端关节，不参与调参)
 *
 * 默认值参考 joint_limits.yaml 的实测数据。
 */
export const JOINT_SCHEMAS: JointSchema[] = [
  {
    jointName: 'J1',
    params: [
      { key: 'kp', label: 'Kp', type: 'slider', min: 0, max: 100, step: 0.1, defaultValue: 1.0, unit: '' },
      { key: 'kd', label: 'Kd', type: 'slider', min: 0, max: 10, step: 0.01, defaultValue: 0.01, unit: '' },
      { key: 'torque_limit', label: '力矩限幅', type: 'slider', min: 0, max: 10, step: 0.1, defaultValue: 1.0, unit: 'Nm' },
      { key: 'max_velocity', label: '最大速度', type: 'slider', min: 0, max: 5, step: 0.01, defaultValue: 2.175, unit: 'rad/s' },
      { key: 'max_acceleration', label: '最大加速度', type: 'slider', min: 0, max: 10, step: 0.01, defaultValue: 3.75, unit: 'rad/s²' },
    ],
  },
  {
    jointName: 'J2',
    params: [
      { key: 'kp', label: 'Kp', type: 'slider', min: 0, max: 100, step: 0.1, defaultValue: 1.0, unit: '' },
      { key: 'kd', label: 'Kd', type: 'slider', min: 0, max: 10, step: 0.01, defaultValue: 0.01, unit: '' },
      { key: 'torque_limit', label: '力矩限幅', type: 'slider', min: 0, max: 10, step: 0.1, defaultValue: 1.0, unit: 'Nm' },
      { key: 'max_velocity', label: '最大速度', type: 'slider', min: 0, max: 5, step: 0.01, defaultValue: 2.175, unit: 'rad/s' },
      { key: 'max_acceleration', label: '最大加速度', type: 'slider', min: 0, max: 10, step: 0.01, defaultValue: 1.875, unit: 'rad/s²' },
    ],
  },
  {
    jointName: 'J3',
    params: [
      { key: 'kp', label: 'Kp', type: 'slider', min: 0, max: 100, step: 0.1, defaultValue: 1.0, unit: '' },
      { key: 'kd', label: 'Kd', type: 'slider', min: 0, max: 10, step: 0.01, defaultValue: 0.01, unit: '' },
      { key: 'torque_limit', label: '力矩限幅', type: 'slider', min: 0, max: 10, step: 0.1, defaultValue: 1.0, unit: 'Nm' },
      { key: 'max_velocity', label: '最大速度', type: 'slider', min: 0, max: 5, step: 0.01, defaultValue: 2.175, unit: 'rad/s' },
      { key: 'max_acceleration', label: '最大加速度', type: 'slider', min: 0, max: 10, step: 0.01, defaultValue: 2.5, unit: 'rad/s²' },
    ],
  },
  {
    jointName: 'J4',
    params: [
      { key: 'kp', label: 'Kp', type: 'slider', min: 0, max: 100, step: 0.1, defaultValue: 1.0, unit: '' },
      { key: 'kd', label: 'Kd', type: 'slider', min: 0, max: 10, step: 0.01, defaultValue: 0.01, unit: '' },
      { key: 'torque_limit', label: '力矩限幅', type: 'slider', min: 0, max: 10, step: 0.1, defaultValue: 1.0, unit: 'Nm' },
      { key: 'max_velocity', label: '最大速度', type: 'slider', min: 0, max: 5, step: 0.01, defaultValue: 2.175, unit: 'rad/s' },
      { key: 'max_acceleration', label: '最大加速度', type: 'slider', min: 0, max: 10, step: 0.01, defaultValue: 3.125, unit: 'rad/s²' },
    ],
  },
  {
    jointName: 'J5',
    params: [
      { key: 'kp', label: 'Kp', type: 'slider', min: 0, max: 100, step: 0.1, defaultValue: 1.0, unit: '' },
      { key: 'kd', label: 'Kd', type: 'slider', min: 0, max: 10, step: 0.01, defaultValue: 0.01, unit: '' },
      { key: 'torque_limit', label: '力矩限幅', type: 'slider', min: 0, max: 10, step: 0.1, defaultValue: 1.0, unit: 'Nm' },
      { key: 'max_velocity', label: '最大速度', type: 'slider', min: 0, max: 5, step: 0.01, defaultValue: 2.61, unit: 'rad/s' },
      { key: 'max_acceleration', label: '最大加速度', type: 'slider', min: 0, max: 10, step: 0.01, defaultValue: 3.75, unit: 'rad/s²' },
    ],
  },
];

/** 根据 Schema 初始化所有关节参数的默认值 Map */
export function buildDefaultValues(schemas: JointSchema[]): Map<string, Map<string, number>> {
  const result = new Map<string, Map<string, number>>();
  for (const joint of schemas) {
    const paramMap = new Map<string, number>();
    for (const param of joint.params) {
      paramMap.set(param.key, param.defaultValue);
    }
    result.set(joint.jointName, paramMap);
  }
  return result;
}
