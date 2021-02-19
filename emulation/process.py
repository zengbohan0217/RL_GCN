import simpy
import random
import time
from model.DQN import *

map = {"1": {'attri': "central_warehouse", 'dis': {"1": 0, "2": 10, "3": 3, "4": 7, "5": 6}},
       "2": {'attri': "central_warehouse", 'dis': {"1": 10, "2": 0, "3": 4, "4": 8, "5": 7}},
       "3": {'attri': "Mater_dist", 'dis': {"1": 3, "2": 4, "3": 0, "4": 5, "5": 4}},
       "4": {'attri': "disa_area", 'dis': {"1": 7, "2": 8, "3": 5, "4": 0, "5": 9}},
       "5": {'attri': "disa_area", 'dis': {"1": 6, "2": 7, "3": 4, "4": 9, "5": 0}}
       }

graph = [[0, 10, 3, 7, 6],
         [10, 0, 4, 8, 7],
         [3, 4, 0, 5, 4],
         [7, 8, 5, 0, 9],
         [6, 7, 4, 9, 0]]
feature_size = 4         # DQN参数
hidden_num = 32          # DQN参数

class central_warehouse(object):
    # 中央储备库，物资由此处送往物资分配中心
    def __init__(self, env, item_num, number):
        """
        :param env: 进程
        :param item_num: 储备库所有物资数目
        :param number: 储备库编号
        """
        self.env = env
        # self.item = simpy.Store(env)
        self.item_num = item_num
        self.number = number

    # def call_for_item(self, car, item_num):
    #     if self.item_num >= item_num:
    #         car.item_num += item_num
    #         self.item_num -= item_num
    #     else:
    #         car.item_num += self.item_num
    #         self.item_num -= 0
    #     print(f"station {self.number} upload the car {car.car_number} in {self.env.now}")

    def call_for_item(self, car):
        if self.item_num >= car.carry_max - car.item_num:
            car.item_num = car.carry_max
            self.item_num -= car.carry_max - car.item_num
        else:
            car.item_num += self.item_num
            self.item_num = 0
        print(f"station {self.number} upload the car {car.car_number} in {self.env.now}")

    def supplement(self, item_num):
        print(f"station {self.number} get new supplement in {self.env.now}")
        self.item_num += item_num


class Material_Redistribution(object):
    # 物资分配中心，物资由此处送往各个受灾点
    def __init__(self, env, item_num, number):
        self.env = env
        self.item_num = item_num
        self.number = number

    def get_item(self, car):
        self.item_num += car.item_num
        car.item_num = 0

    def serve_car(self, car):
        if self.item_num >= car.carry_max - car.item_num:
            car.item_num = car.carry_max
            self.item_num -= car.carry_max - car.item_num
        else:
            car.item_num += self.item_num
            self.item_num = 0


class disaster_area(object):
    # 受灾点，物资将被最终送往这里
    def __init__(self, env, need_item, number):
        self.env = env
        self.need_item = need_item
        self.now_item = 0
        self.serve = 0
        self.number = number

    def get_item(self, car):
        if car.item_num > self.need_item - self.now_item:
            car.item_num -= self.need_item - self.now_item
            self.now_item = self.need_item
        else:
            car.item_num = 0
            self.now_item += self.need_item
        self.serve = self.now_item/self.need_item
        print(f"disaster area {self.number} get the car {car.car_number} serve in {self.env.now}")

class carry_all(object):
    # 运输车，运送物资的载具
    # 可在中央存储库到分配中心之间运输，也可在分配中心到受灾地之间运输
    def __init__(self, env, carry_max, car_number, start_place):
        self.env = env
        self.carry_max = carry_max
        self.item_num = 0
        self.car_number = car_number
        self.start_place = start_place
        self.now_place = start_place
        self.flag = 0                 # 判断是否处于运输状态

    def trans(self, start_pos, end_pos):
        self.flag = 1
        yield self.env.timeout(map[str(start_pos)]['dis'][str(end_pos)])
        self.now_place = end_pos
        self.flag = 0


def setup(env, car_num):
    car_list = []    # 创建若干个运输车
    for i in range(car_num):
        carry_max = random.randint(50, 100)
        start_place = random.randint(1, 2)
        car = carry_all(env, carry_max, i+1, start_place)
        car_list.append(car)

    place_dic = {}
    place_dic['1'] = central_warehouse(env, 300, 1)
    place_dic['2'] = central_warehouse(env, 400, 2)
    place_dic['3'] = Material_Redistribution(env, 50, 3)
    place_dic['4'] = disaster_area(env, 300, 4)
    place_dic['5'] = disaster_area(env, 200, 5)

    model = DQN(graph=graph, point_num=5, batch_size=16, batch_num=2, in_c=feature_size, hid_c=hidden_num)
    memory = []         # DQN经验池
    epoch = 0           # 记录第几轮用于epsilon greedy
    ########### epsilon参数
    start_eps = 1.0
    end_eps = 0.1
    start_decay_epoch = 0
    end_decay_epoch = 50
    ###########

    while True:
        yield env.timeout(1)
        for i in range(car_num):
            if car_list[i].flag == 0:
                if map[str(car_list[i].now_place)]['attri'] == 'central_warehouse':
                    # env.process(place_dic[str(car_list[i].now_place)].call_for_item(car_list[i]))
                    place_dic[str(car_list[i].now_place)].call_for_item(car_list[i])
                    next_place = random.randint(1, 5)
                    epoch += 1
                    curr_eps = get_epsilon(epoch, end_decay_epoch, start_decay_epoch, start_eps=start_eps,
                                           end_eps=end_eps)
                    env.process(car_list[i].trans(car_list[i].now_place, next_place))

                elif map[str(car_list[i].now_place)]['attri'] == 'Mater_dist':
                    # env.process(place_dic[str(car_list[i].now_place)].get_item(car_list[i]))
                    # env.process(place_dic[str(car_list[i].now_place)].serve_car(car_list[i]))
                    place_dic[str(car_list[i].now_place)].get_item(car_list[i])
                    place_dic[str(car_list[i].now_place)].serve_car(car_list[i])
                    next_place = random.randint(1, 5)
                    epoch += 1
                    curr_eps = get_epsilon(epoch, end_decay_epoch, start_decay_epoch, start_eps=start_eps,
                                           end_eps=end_eps)
                    env.process(car_list[i].trans(car_list[i].now_place, next_place))

                elif map[str(car_list[i].now_place)]['attri'] == 'disa_area':
                    # env.process(place_dic[str(car_list[i].now_place)].get_item(car_list[i]))
                    place_dic[str(car_list[i].now_place)].get_item(car_list[i])
                    next_place = random.randint(1, 5)
                    epoch += 1
                    curr_eps = get_epsilon(epoch, end_decay_epoch, start_decay_epoch, start_eps=start_eps,
                                           end_eps=end_eps)
                    env.process(car_list[i].trans(car_list[i].now_place, next_place))
        #time.sleep(1)
        print(f"currant epsilon is {curr_eps}")
        print(f"disa_1 serve: {place_dic['4'].serve}")
        print(f"disa_1 serve: {place_dic['5'].serve}")

env = simpy.Environment()
env.process(setup(env, 3))
env.run(until=100)

