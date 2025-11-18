// src/index.js
import express from 'express';
import bodyParser from 'body-parser';
import amqp from 'amqplib';

const app = express();
app.use(bodyParser.json());

const PORT = process.env.PORT || 3001;
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://localhost:5672';
const QUEUE_ORDERS = process.env.QUEUE_ORDERS || 'orders';

let channel;
const orders = [];

async function initRabbit() {
  const conn = await amqp.connect(RABBITMQ_URL);
  channel = await conn.createChannel();
  await channel.assertQueue(QUEUE_ORDERS, { durable: true });
  console.log(`RabbitMQ conectado. Fila: ${QUEUE_ORDERS}`);
}

app.get('/health', (_, res) => res.json({ status: 'ok' }));

app.get('/orders', (_, res) => res.json({ orders }));

app.post('/orders', async (req, res) => {
  const order = req.body;
  if (!order || !order.id) {
    return res.status(400).json({ error: 'Pedido inválido: informar id' });
  }
  orders.push({ ...order, status: 'created' });
  const msg = Buffer.from(JSON.stringify(order));
  await channel.sendToQueue(QUEUE_ORDERS, msg, { persistent: true });
  return res.status(201).json({ message: 'Pedido criado e enfileirado', order });
});

app.listen(PORT, async () => {
  try {
    await initRabbit();
    console.log(`Service-order ouvindo em http://localhost:${PORT}`);
  } catch (err) {
    console.error('Falha ao conectar ao RabbitMQ:', err.message);
    process.exit(1);
  }
});
