# Ecommerce Analytics Schema / 电商分析数据库 Schema

## Table: users

中文名 / Chinese name: 用户表  
英文名 / English name: users

业务含义 / Business meaning:
users 表存储用户的基础画像信息。  
The users table stores basic user profile information.

字段说明 / Fields:
- user_id: 用户唯一 ID，主键。Unique user ID. Primary key.
- username: 用户显示名称或昵称。User display name.
- gender: 用户性别。User gender.
- age: 用户年龄。User age.
- city: 用户所在城市。User's city.
- register_time: 用户注册时间。User registration time.

常见问题 / Common questions:
- 每个城市有多少用户？How many users are in each city?
- 最近新增注册用户有多少？How many new users registered recently?
- 用户年龄分布是什么样的？What is the user age distribution?

## Table: products

中文名 / Chinese name: 商品表  
英文名 / English name: products

业务含义 / Business meaning:
products 表存储商品目录和商品基础信息。  
The products table stores product catalog information.

字段说明 / Fields:
- product_id: 商品唯一 ID，主键。Unique product ID. Primary key.
- product_name: 商品名称。Product name.
- category: 商品类目，例如 数码、服饰、美妆、食品、家居、图书、运动、母婴。Product category, such as 数码, 服饰, 美妆, 食品, 家居, 图书, 运动, 母婴.
- price: 商品标价或列表价。Product list price.
- created_time: 商品创建时间或上架时间。Product created or listed time.

常见问题 / Common questions:
- 哪个商品类目的销量最高？Which product category has the highest sales?
- 哪些商品的销售额最高？Which products have the highest sales amount?
- 每个类目下有多少商品？How many products are in each category?

## Table: orders

中文名 / Chinese name: 订单表  
英文名 / English name: orders

业务含义 / Business meaning:
orders 表存储订单级别的交易数据，一行代表一个订单。  
The orders table stores order-level transaction data. Each row represents one order.

字段说明 / Fields:
- order_id: 订单唯一 ID，主键。Unique order ID. Primary key.
- user_id: 下单用户 ID，外键，关联 users.user_id。User who placed the order. Foreign key to users.user_id.
- order_time: 订单创建时间或下单时间。Time when the order was created.
- status: 订单状态。可能的取值包括 created、paid、cancelled、refunded。Order status. Possible values: created, paid, cancelled, refunded.
- total_amount: 订单总金额，用于 GMV、销售额、用户消费金额等统计。Total order amount, used for GMV, revenue, and user spending analysis.
- city: 下单城市或订单所属城市。City where the order was placed.

指标口径 / Metric definitions:
- GMV: 默认指已支付订单的 total_amount 之和，即 status = 'paid' 的订单金额总和，除非问题中另有说明。Sum of total_amount from paid orders unless otherwise specified.
- 支付订单数 / Paid order count: status = 'paid' 的订单数量。Count of orders where status = 'paid'.
- 客单价 / Average order value: 已支付订单的 total_amount 之和除以支付订单数。Sum of total_amount for paid orders divided by paid order count.

常见问题 / Common questions:
- 每个城市的 GMV 是多少？What is the GMV by city?
- 每天产生了多少订单？How many orders were placed each day?
- 支付 GMV 最高的城市有哪些？What are the top cities by paid GMV?

## Table: order_items

中文名 / Chinese name: 订单明细表  
英文名 / English name: order_items

业务含义 / Business meaning:
order_items 表存储订单中的商品明细数据，一行代表一个订单里的一个商品条目。  
The order_items table stores item-level details within each order.

字段说明 / Fields:
- item_id: 订单明细唯一 ID，主键。Unique order item ID. Primary key.
- order_id: 所属订单 ID，外键，关联 orders.order_id。Related order ID. Foreign key to orders.order_id.
- product_id: 商品 ID，外键，关联 products.product_id。Related product ID. Foreign key to products.product_id.
- quantity: 该商品在订单中的购买数量，用于统计销量。Quantity of the product in the order, used for sales volume analysis.
- unit_price: 下单时的商品单价。Product unit price when the order was placed.
- amount: 订单明细金额，通常等于 quantity * unit_price。Item amount, usually quantity * unit_price.

常见问题 / Common questions:
- 哪些商品的销售额最高？Which products have the highest sales amount?
- 哪些商品类目的销售额最高？Which categories have the highest sales amount?
- 每个商品的总销售数量是多少？What is the total quantity sold for each product?

## Table: user_events

中文名 / Chinese name: 用户行为事件表  
英文名 / English name: user_events

业务含义 / Business meaning:
user_events 表存储用户在商品上的行为事件数据，例如浏览、加购、收藏、购买等。  
The user_events table stores user behavior events on products.

字段说明 / Fields:
- event_id: 用户行为事件唯一 ID，主键。Unique event ID. Primary key.
- user_id: 发生该行为的用户 ID，外键，关联 users.user_id。User who performed the event. Foreign key to users.user_id.
- product_id: 行为关联的商品 ID，外键，关联 products.product_id。Product related to the event. Foreign key to products.product_id.
- event_type: 行为事件类型。可能的取值包括 view、cart、favorite、purchase。Event type. Possible values: view, cart, favorite, purchase.
- event_time: 行为发生时间。Time when the event happened.

指标口径 / Metric definitions:
- PV / 浏览量: 浏览事件数量，即 event_type = 'view' 的事件数。Count of view events.
- 加购次数 / Add-to-cart count: event_type = 'cart' 的事件数。Count of cart events.
- 购买行为次数 / Purchase event count: event_type = 'purchase' 的事件数。Count of purchase events.
- 行为转化率 / Behavior conversion rate: 通常指 purchase 事件数除以 view 事件数，具体口径取决于用户问题上下文。Purchase events divided by view events, depending on the question context.

常见问题 / Common questions:
- 哪些商品的浏览量最高？Which products have the most views?
- 哪些商品类目的加购次数最多？Which categories have the most cart events?
- 每个商品的购买转化率是多少？What is the purchase conversion rate by product?

## 表关系说明 / Relationships

- orders.user_id -> users.user_id：一个用户可以有多个订单。One user can place multiple orders.
- order_items.order_id -> orders.order_id：一个订单可以包含多个商品明细。One order can contain multiple order items.
- order_items.product_id -> products.product_id：一个商品可以出现在多个订单明细中。One product can appear in multiple order items.
- user_events.user_id -> users.user_id：一个用户可以产生多个行为事件。One user can generate multiple behavior events.
- user_events.product_id -> products.product_id：一个商品可以被多个用户浏览、加购、收藏或购买。One product can be viewed, added to cart, favorited, or purchased by multiple users.

## 常用分析路径 / Common Analysis Paths

- 分析用户订单或用户消费金额时，通常使用 users join orders，连接条件为 users.user_id = orders.user_id。For user order or spending analysis, usually join users and orders on users.user_id = orders.user_id.
- 分析商品销量或商品销售额时，通常使用 order_items join products，连接条件为 order_items.product_id = products.product_id。For product sales volume or sales amount analysis, usually join order_items and products on order_items.product_id = products.product_id.
- 分析按时间筛选的商品销售时，通常使用 order_items join orders，再通过 orders.order_time 过滤时间。For time-based product sales analysis, usually join order_items and orders, then filter by orders.order_time.
- 分析商品类目的销售额时，通常使用 order_items join products，并按 products.category 分组。For category sales amount analysis, usually join order_items and products, then group by products.category.
- 分析用户行为转化时，通常使用 user_events，并根据 event_type 区分 view、cart、favorite、purchase。For behavior conversion analysis, usually use user_events and distinguish view, cart, favorite, and purchase by event_type.
