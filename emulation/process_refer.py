import model.DQN
import random
import simpy

# 可接受输入参数
RANDOM_SEED = 0  # 不设置
NUM_MACHINES = 2  # 可以同时处理的机器数（类似工作工位数）
TIME_CONSUMING = 5  # 单任务耗时 (可以设计成随机数)
TIME_INTERVAL = 5  # 来车的间隔时间约5分钟   (可以设计成随机数)
SIM_TIME = 1000  # 仿真总时间
CLIENT_NUMBER = 10  # 初始时已经占用机器数
STATION_NUM = 8  # 服务站个数


class WorkStation(object):
    """
    一个工作站，拥有特定数量的机器数。 一个客户首先申请服务。在对应服务时间完成后结束并离开工作站
    """

    def __init__(self, env, num_machines, washtime, list_num):
        self.env = env
        self.machine = simpy.Resource(env, num_machines)
        self.washtime = washtime
        self.allClient = 0
        self.accomplishClient = 0
        self.list_num = list_num

    def wash(self, car):
        """服务流程"""
        yield self.env.timeout(random.randint(2, 10))  # 假设服务时间为随机数（2~10）
        self.allClient += 1
        per = random.randint(50, 99)
        print("%s's 任务完成度：%d%%." % (car, per))
        if per > 80:
            self.accomplishClient += 1

        print("工作站服务客户数：%d,"
              "工作站服务达标率：%.2f。" % (self.allClient, float(self.accomplishClient) / float(self.allClient)))


def Client(env, name, cw):
    """
    客户到达动作站接受服务，结束后离开
    """

    print('%s 到达工作站 at %.2f.' % (name, env.now))
    with cw.machine.request() as request:
        yield request
        print('%s 接受服务   at %.2f. in %d' % (name, env.now, cw.list_num))
        yield env.process(cw.wash(name))
        print('%s 离开服务站 at %.2f. in %d' % (name, env.now, cw.list_num))


class client(object):
    def __init__(self, env, name, cw):
        self.env = env
        self.name = name
        self.work_station = cw
        self.work_place = cw.list_num

    def serv(self):
        print('%s 到达工作站 at %.2f.' % (self.name, env.now))
        with self.work_station.machine.request() as request:
            yield request
            print('%s 接受服务   at %.2f. in %d' % (self.name, env.now, self.work_station.list_num))
            yield env.process(self.work_station.wash(self.name))
            print('%s 离开服务站 at %.2f. in %d' % (self.name, env.now, self.work_station.list_num))

def Setup(env, num_machines, washtime, t_inter, clientNumber, list_num):
    """创建一个工作站，几个初始客户，然后持续有客户到达. 每隔t_inter - 2, t_inter + 3分钟（可以自定义）."""
    # 创建工作站
    workstation = WorkStation(env, num_machines, washtime, list_num)

    # 创建clientNumber个初始客户
    for i in range(clientNumber):
        env.process(Client(env, 'Client_%d' % i, workstation))

    # 在仿真过程中持续创建客户
    while True:
        yield env.timeout(random.randint(t_inter - 2, t_inter + 3))  # 3-8分钟
        i += 1
        env.process(Client(env, 'Client_%d' % i, workstation))


def setup(env, num_machine, washtime, t_inter, clientNumber, work_station_num):
    """创建若干个工作站，几个用户，接着持续有用户到达"""
    # 创建若干个工作站
    station_list = []
    for i in range(work_station_num):
        work_station = WorkStation(env, num_machine, washtime, i)
        station_list.append(work_station)
    # 创建若干个初始用户
    for i in range(clientNumber):
        station_num = random.randint(0, 7)
        client_sample = client(env, 'Client_%d' % i, station_list[station_num])
        env.process(client_sample.serv())
    # 持续创建用户
    while True:
        yield env.timeout(random.randint(t_inter - 2, t_inter + 3))
        i += 1
        station_num = random.randint(0, 7)
        client_sample = client(env, 'Client_%d' % i, station_list[station_num])
        env.process(client_sample.serv())


# 初始化并开始仿真任务
print('开始仿真')

# 初始化seed，指定数值的时候方正结果可以复现
random.seed()

# 创建一个环境并开始仿真
env = simpy.Environment()
# for i in range(STATION_NUM):
#     env.process(Setup(env, NUM_MACHINES, TIME_CONSUMING, TIME_INTERVAL, CLIENT_NUMBER, i))
env.process(setup(env, NUM_MACHINES, TIME_CONSUMING, TIME_INTERVAL, CLIENT_NUMBER, STATION_NUM))

# 开始执行!
env.run(until=SIM_TIME)

