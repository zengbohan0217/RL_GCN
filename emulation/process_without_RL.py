import simpy
import random
import time

# map = {"1": {'attri': "central_warehouse", 'dis': {"1": 0, "2": 10, "3": 3, "4": 7, "5": 6}},
#        "2": {'attri': "central_warehouse", 'dis': {"1": 10, "2": 0, "3": 4, "4": 8, "5": 7}},
#        "3": {'attri': "Mater_dist", 'dis': {"1": 3, "2": 4, "3": 0, "4": 5, "5": 4}},
#        "4": {'attri': "disa_area", 'dis': {"1": 7, "2": 8, "3": 5, "4": 0, "5": 9}},
#        "5": {'attri': "disa_area", 'dis': {"1": 6, "2": 7, "3": 4, "4": 9, "5": 0}}
#        }

# 设计思路 应该为运输车甲、运输车乙分别设计地图，因此应该把三种属性图分开

map_cwh = {"1": {"1": 3},
           "2": {"1": 4}}      # 代表中央储备库1号与2号和物资分配中心1号之间的距离

map_da = {"1": {"1": 5},
          "2": {"1": 4}}       # 代表受灾地1号与2号和物资分配中心1号之间的距离


class central_warehouse(object):
    # 中央存储库，资源无限，可以一直满足需求，运输车甲在此与物资分配中心之间相互运输
    def __init__(self, env, number):
        """
        :param env: 进程
        :param number: 地点编号
        """
        self.env = env
        self.number = number
        self.car_num = 0
        # self.car_list = []
        # self.flag_load = 0


class Material_Redistribution(object):
    # 物资分配中心，存储有上限，运输车乙由此与受灾点之间相互运输
    def __init__(self, env, item_max, number):
        """
        :param env:
        :param item_max:资源存储上限
        :param number:
        """
        self.env = env
        self.item_num = 0               # 现有资源
        self.item_max = item_max
        self.number = number


class disaster_area(object):
    # 受灾地，存储无上限
    def __init__(self, env, item_need, number, item_rate):
        """
        :param env:
        :param item_need: 需要物资
        :param number: 受灾地编号
        :param item_rate: 物资消耗速率
        """
        self.env = env
        self.item_need = item_need
        self.item_rate = item_rate
        self.number = number
        self.item_num = 0               # 现有资源


class carry_all_0(object):
    # 运输车甲，在中央储备库和物资调度中心之间运转
    def __init__(self, env, carry_max, base_speed, place_num, car_num):
        """
        :param env: 进程
        :param carry_max: 车辆最大配重
        :param base_speed: 基础速度，随路段情况变化
        :param place_num: 定义运输车初始在哪个中央储备库
        """
        self.env = env
        self.car_num = car_num          # 运输车甲编号
        self.road_level = 1             # 道路等级，根据map来转变
        self.carry_max = carry_max
        self.item_now = 0               # 当前运输车的载重
        self.now_place_type = "central_warehouse"
        self.now_place_num = place_num
        self.base_speed = base_speed
        self.base_count = 1             # 假设基础油耗为1升
        self.flag_load = 0              # 装卸进程管理
        self.flag_trans = 0             # 运输车移动进程管理

    def upload_car(self):
        # 由于同时装卸货车辆数目不做限制，因此就在运输车类里进行装卸货，并且中央储备库物资无限
        self.flag_load = 1
        yield self.env.timeout(1)       # 装卸货所需时间为0.5小时
        print(f"car_0 {self.car_num} finish upload at {self.now_place_type} {self.now_place_num}")
        self.item_now = self.carry_max
        self.flag_load = 0

    def down_load(self, MR):
        # 当运输车甲抵达物资调度中心后开始卸货
        self.flag_load = 1
        yield self.env.timeout(1)       # 装卸货所需时间为0.5小时
        print(f"car_0 {self.car_num} finish download at {self.now_place_type} {self.now_place_num}")
        if self.item_now > MR.item_max - MR.item_num:
            self.item_now -= MR.item_max - MR.item_num
            MR.item_num = MR.item_max
        else:
            MR.item_num += self.item_now
            self.item_now = 0
        self.flag_load = 0


    def trans(self, start_pos, end_pos, end_pos_type):
        """
        :param start_pos: 出发点编号
        :param end_pos: 目的地编号
        :param end_pos_type: 目的地类型，包括了中央储备库和物资调度中心
        :return:
        """
        self.flag_trans = 1
        if self.road_level == 1:
            if self.now_place_type == "central_warehouse":
                print(f"start trans from cwh {start_pos} to MR {end_pos}")
                yield self.env.timeout(map_cwh[str(start_pos)][str(end_pos)] / self.base_speed)
            elif self.now_place_type == "Material_Redistribution":
                print(f"start trans from MR {start_pos} to cwh {end_pos}")
                yield self.env.timeout(map_cwh[str(end_pos)][str(start_pos)] / self.base_speed)
        # 等级2 3尚未构建
        print(f"arrive at {end_pos_type} {end_pos}")
        self.now_place_type = end_pos_type  # 地点类型转换
        self.now_place_num = end_pos        # 地点编号转换
        self.flag_trans = 0



