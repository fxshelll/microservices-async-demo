// src/index.js
import express from 'express';
import amqp from 'amqplib';

const app = express();
const PORT = process.env.PORT || 3002;
const RABBITMQ_URL = process.env.RABBITMQ_URL || 'amqp://localhost:5672';
const QUEUE_ORDERS = process.env.QUEUE_ORDERS || 'orders';

const payments = [];

async function startConsumer() {
  const conn = await amqp.connect(RABBITMQ_URL);
  const channel = await conn.createChannel();
  await channel.assertQueue(QUEUE_ORDERS, { durable: true });
  await channel.prefetch(1);

  console.log(`Consumindo fila: ${QUEUE_ORDERS}`);
  channel.consume(QUEUE_ORDERS, async (msg) => {
    try {
      const order = JSON.parse(msg.content.toString());
      // Simula processamento
      await new Promise((r) => setTimeout(r, 500));
      payments.push({ orderId: order.id, status: 'paid', ts: new Date().toISOString() });
      channel.ack(msg);
      console.log(`Pagamento processado para pedido ${order.id}`);
    } catch (err) {
      console.error('Erro no processamento:', err.message);
      channel.nack(msg, false, true); // reencaminha para a fila
    }
  });
}

app.get('/health', (_, res) => res.json({ status: 'ok' }));
app.get('/payments', (_, res) => res.json({ payments }));

app.listen(PORT, async () => {
  try {
    await startConsumer();
    console.log(`Service-payment ouvindo em http://localhost:${PORT}`);
  } catch (err) {
    console.error('Falha ao iniciar consumidor:', err.message);
    process.exit(1);
  }
});
