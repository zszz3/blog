---
title: RocketMQ
published: 2025-06-01
description: ''
image: ''
tags: [Java,'中间件']
category: 'Notes'
draft: false 
lang: ''
---

**消息队列**

消息队列是一种用于异步通信的机制，允许不同的系统组件或服务之间交换信息。它的主要作用是将消息从发送者传递到接收者，同时解耦这两个组件的直接依赖。
![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250520171823.png)

而RocketMQ是一个开源的分布式消息中间件，它主要用于高吞吐量、低延迟的消息传递需求。
![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250520172211.png)

# 1.什么场景下用RocketMQ
## 1.1 异步解耦
最常见的一个场景是用户注册后，需要发送注册邮件和短信通知，以告知用户注册成功（注册系统处理完之后就注册成功了）。
串行方式：
![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250520174823.png)
数据流动如下所述：
- 注册页面填写账号和密码并提交注册信息，这些注册信息首先会被写入注册系统。
- 注册信息写入注册系统成功后，再发送请求至邮件通知系统。邮件通知系统收到请求后向用户发送邮件通知。
- 邮件通知系统接收注册系统请求后再向下游的短信通知系统发送请求。短信通知系统收到请求后向用户发送短信通知。
以上三个任务全部完成后，才返回注册结果到客户端，用户才能使用账号登录。假设每个任务耗时分别为 50ms，则用户需要在注册页面等待总共 150ms 才能登录。

并行形式：
![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250521162414.png)
数据流动如下所述：
- 用户在注册页面填写账号和密码并提交注册信息，这些注册信息首先会被写入注册系统。
- 注册信息写入注册系统成功后，再同时发送请求至邮件和短信通知系统。邮件和短信通知系统收到请求后分别向用户发送邮件和短信通知。
以上两个任务全部完成后，才返回注册结果到客户端，用户才能使用账号登录。
假设每个任务耗时分别为50ms，其中，邮件和短信通知并行完成，则用户需要在注册页面等待总共100ms才能登录。

**异步解耦**
对于用户来说，注册功能实际只需要注册系统存储用户的账户信息后，该用户便可以登录，后续的注册短信和邮件不是即时需要关注的步骤。
对于注册系统而言，发送注册成功的短信和邮件通知并不一定要绑定在一起同步完成，所以实际当数据写入注册系统后，注册系统就可以把其他的操作放入对应的 RocketMQ 中然后马上返回用户结果，由 RocketMQ 异步地进行这些操作。
![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250520192234.png)
数据流动如下所述：
- 用户在注册页面填写账号和密码并提交注册信息，这些注册信息首先会被写入注册系统
- 注册信息写入注册系统成功后，再发送消息至 RocketMQ。 RocketMQ 会马上返回响应给注册系统，注册完成。用户可立即登录。
- 下游的邮件和短信通知系统订阅 RocketMQ 的此类注册请求消息，即可向用户发送邮件和短信通知，完成所有的注册流程
用户只需在注册页面等待注册数据写入注册系统和 RocketMQ 的时间，即等待 55ms 即可登录。

## 1.2 削峰填谷
在秒杀或团队抢购活动中，由于用户请求量较大，导致流量暴增，秒杀的应用在处理如此大量的访问流量后，下游的通知系统无法承载海量的调用量，甚至会导致系统崩溃等问题而发生漏通知的情况。为解决这些问题，可在应用和下游通知系统之间加入 RocketMQ。
![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250520200026.png)
秒杀处理流程如下所述：
- 用户发起海量秒杀请求到秒杀业务处理系统。
- 秒杀处理系统按照秒杀处理逻辑将满足秒杀条件的请求发送 RocketMQ。
- 下游的通知系统订阅 RocketMQ 的秒杀相关消息，再将秒杀成功的消息发送到相应用户。
- 用户收到秒杀成功的通知。

## 1.3 顺序消息
顺序消息是 RocketMQ 提供的一种对消息发送和消费顺序有严格要求的消息。

对于一个指定的 Topic，消息严格按照先进先出（FIFO）的原则进行消息发布和消费，即先发布的消息先消费，后发布的消息后消费。
**顺序消息分为分区顺序消息和全局顺序消息。**
- 分区顺序消息：对于指定的一个 Topic，所有消息根据 Sharding Key 进行区块分区，同一个分区内的消息按照严格的先进先出（FIFO）原则进行发布和消费。同一分区内的消息保证顺序，不同分区之间的消息顺序不做要求。
    - 适用场景：适用于性能要求高，以 Sharding Key 作为分区字段，在同一个区块中严格地按照先进先出（FIFO）原则进行消息发布和消费的场景。
    - 示例
        - 用户注册需要发送验证码，以用户 ID 作为 Sharding Key，那么同一个用户发送的消息都会按照发布的先后顺序来消费。
        - 电商的订单创建，以订单 ID 作为 Sharding Key，那么同一个订单相关的创建订单消息、订单支付消息、订单退款消息、订单物流消息都会按照发布的先后顺序来消费。
- 全局顺序消息：对于指定的一个Topic，所有消息按照严格的先入先出（FIFO）的顺序来发布和消费。
    - 适用场景：适用于性能要求不高，所有的消息严格按照 FIFO 原则来发布和消费的场景。
    - 示例：在证券处理中，以人民币兑换美元为 Topic，在价格相同的情况下，先出价者优先处理，则可以按照 FIFO 的方式发布和消费全局顺序消息。

全局顺序消息实际上是一种特殊的分区顺序消息，即 Topic 中只有一个分区，因此全局顺序和分区顺序的实现原理相同。因为分区顺序消息有多个分区，所以分区顺序消息比全局顺序消息的并发度和性能更高。
![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250521162701.png)


## 1.4 分布式缓存同步
双十一大促时，各个分会场会有琳琅满目的商品，每件商品的价格都会实时变化。使用缓存技术也无法满足对商品价格的访问需求，缓存服务器网卡满载。访问较多次商品价格查询影响会场页面的打开速度。
此时需要提供一种广播机制，一条消息本来只可以被集群的一台机器消费，如果使用 RocketMQ 的广播消费模式，那么这条消息会被所有节点消费一次，相当于把价格信息同步到需要的每台机器上，取代缓存的作用。
![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250521163021.png)

## 1.5 分布式定时/延时调度
![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250521163102.png)

# 2. RocketMQ基础概念

## 主题 Topic
主题是RocketMQ中消息传递喝存储的顶层容器，用于标识同一类业务逻辑的消息。主题的作用主要如下：
- 定义数据的分类隔离：**将不同业务类型的数据拆分到不同的主题中管理，通过主题实现存储的隔离性和订阅隔离性**
- 定义数据的身份和权限：RocketMQ 的消息本身是匿名无身份的，同一分类的消息使用相同的主题来做身份识别和权限管理。

![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250521110803.png)

## 队列 Queue
队列是RocketMQ中消息存储和传输的实际容器，也是RocketMQ消息的最小存储单元。RocketMQ的所有主题都是由多个队列组成，以此实现队列数量的水平拆分和队列内部的流式存储。
## 消息 Message
消息是RocketMQ中的最小数据传输单元。生产者将业务数据的负载和拓展属性包装成消息发送到RocketMQ服务端，服务端按照相关语义将消息投递到消费端进行消费。
## 生产者 Producer
发布消息的角色。Producer 通过 MQ 的负载均衡模块选择相应的Broker集群队列进行消息投递，投递的过程支持快速失败和重试。
## 消费者 Consumer
消息消费的角色。
- 支持以推（push），拉（pull）两种模式对消息进行消费。
- 同时也支持**集群方式**和广播方式的消费。
- 提供实时消息订阅机制，可以满足大多数用户的需求。
## 名字服务器 NameServer
NameServer是一个简单的Topic路由注册中心，支持Topic、Broker的动态注册和发现。
- **Broker管理：** NameServer 接受 Broker 集群的注册信息并且保存下来作为路由信息的基本数据。然后提供心跳检测机制，检查 Broker 是否还存活；
- **路由信息管理：** 每个 NameServer 将保存关于 Broker 集群的整个路由信息和用于客户端查询的队列信息。Producer 和 Consumer 通过 NameServer 就可以知道整个 Broker 集群的路由信息，从而进行消息的投递和消费。
## 代理服务器 Broker
Broker像“快递员”，主要负责消息的存储、投递和查询以及服务高可用保证。

在Master-Slave架构中，Broker 分为 Master 与 Slave。一个 Master 可以对应多个 Slave，但是一个 Slave 只能对应一个 Master。Master 与 Slave 的对应关系通过指定相同的 BrokerName，不同的 BrokerId 来定义，BrokerId 为 0 表示 Master，非 0 表示 Slave。Master 也可以部署多个。
部署模型小结：
- 每个 **Broker** 与 **NameServer** 集群中的所有节点建立长连接，定时注册 Topic 信息到所有 NameServer。
- **Producer** 与 **NameServer** 集群中的其中一个节点建立长连接，定期从 NameServer 获取 Topic 路由信息，并向提供 Topic 服务的 Master 建立长连接，且定时向 Master 发送心跳。Producer 完全无状态。
- **Consumer** 与 **NameServer** 集群中的其中一个节点建立长连接，定期从 NameServer 获取 Topic 路由信息，并向提供 Topic 服务的 Master、Slave 建立长连接，且定时向 Master、Slave 发送心跳。Consumer 既可以从 Master 订阅消息，也可以从 Slave 订阅消息。

# 3. RocketMQ工作原理
![image.png](https://wojiecihuo-1306847107.cos.ap-nanjing.myqcloud.com/obsidian/20250521164131.png)
**1.启动 NameServer**
启动 NameServer。NameServer 启动后监听端口，等待 Broker、Producer、Consumer 连接，相当于一个路由控制中心。

**2.启动 Broker**
启动 Broker。与所有 NameServer 保持长连接，定时发送心跳包。心跳包中包含当前 Broker 信息以及存储所有 Topic 信息。注册成功后，NameServer 集群中就有 Topic 跟 Broker 的映射关系。

**3.创建 Topic**
创建 Topic 时需要指定该 Topic 要存储在哪些 Broker 上，也可以在发送消息时自动创建 Topic。

 **4.生产者发送消息**
生产者发送消息。启动时先跟 NameServer 集群中的其中一台建立长连接，并从 NameServer 中获取当前发送的 Topic 存在于哪些 Broker 上，轮询从队列列表中选择一个队列，然后与队列所在的 Broker 建立长连接从而向 Broker发消息。

**5.消费者接受消息**
消费者接受消息。跟其中一台 NameServer 建立长连接，获取当前订阅 Topic 存在哪些 Broker 上，然后直接跟 Broker 建立连接通道，然后开始消费消息。

# 4. 动手发一条消息

配置文件中引入RocketMQ相关配置定义，比如连接 NameServer 地址等。
``` xml
rocketmq:  
  name-server: 127.0.0.1:9876 # NameServer 地址，如果 VM 参数里设置了星球云服务器 RocketMQ 地址，运行时会替换  
  producer:  
    # 通用生产者组，其中的 ${unique-name:} 是为了避免大家公用一个 Topic，造成你发的消息被其他同学消费，其他同学发的消息被你消费等问题  
    group: oneCoupon_merchant-admin${unique-name:}-service_common-message-execute_pg   # NameServer 地址  
    send-message-timeout: 2000             # 发送超时时间  
    retry-times-when-send-failed: 1        # 同步发送重试次数  
    retry-times-when-send-async-failed: 1  # 异步发送重试次数
```

定义消息生产者，通过 `RocketMQTemplate` 向 RocketMQ 发送普通常规消息。
``` java
@Slf4j  
@Component  
@RequiredArgsConstructor  
public class GeneralMessageDemoProduce {  
    private final RocketMQTemplate rocketMQTemplate;  
  
    /**  
     * 发送普通消息  
     *  
     * @param topic            消息发送主题，用于标识同一类业务逻辑的消息  
     * @param tag              消息的过滤标签，消费者可通过Tag对消息进行过滤，仅接收指定标签的消息。  
     * @param keys             消息索引键，可根据关键字精确查找某条消息  
     * @param messageBody      普通消息发送事件，自定义对象，最终都会序列化为字符串  
     * @return 消息发送 RocketMQ 返回结果  
     */  
    public SendResult send(String topic, String tag, String keys, JSONObject messageBody) {  
        SendResult sendResult;  
        StringBuilder destinationBuilder = StrUtil.builder().append(topic);  
        if (StrUtil.isNotBlank(tag)) {  
            destinationBuilder.append(":").append(tag);  
        }  
        // 构建消息体  
        Message<?> message = MessageBuilder  
                .withPayload(messageBody)  
                .setHeader(MessageConst.PROPERTY_KEYS, keys)  
                .setHeader(MessageConst.PROPERTY_TAGS, tag)  
                .build();  
        try {  
            sendResult = rocketMQTemplate.syncSend(  
                    destinationBuilder.toString(),  
                    message,  
                    2000L  
            );  
            log.info("[普通消息] 消息发送结果：{}，消息ID：{}，消息Keys：{}", sendResult.getSendStatus(), sendResult.getMsgId(), keys);  
        } catch (Throwable ex) {  
            log.error("[普通消息] 消息发送失败，消息体：{}", messageBody.toString(), ex);  
            throw ex;  
        }  
        return sendResult;  
    }  
}
```