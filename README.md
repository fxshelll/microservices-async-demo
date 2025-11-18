# Microservices Async Demo

Este projeto demonstra uma arquitetura de microsserviços com comunicação assíncrona utilizando RabbitMQ. O objetivo é aplicar os conceitos de desacoplamento, escalabilidade e mensageria aprendidos na disciplina.

## Tecnologias utilizadas
- Node.js com Express
- RabbitMQ (mensageria)
- Docker e Docker Compose
- cURL para testes de API

## Estrutura do Projeto 
```sh
microservices-async-demo/
│
├── docker-compose.yml
├── README.md
│
├── service-order/
│   ├── Dockerfile
│   ├── package.json
│   ├── wait-for-rabbit.sh
│   └── src/
│       └── index.js
│
├── service-payment/
│   ├── Dockerfile
│   ├── package.json
│   ├── wait-for-rabbit.sh
│   └── src/
│       └── index.js
```


## Microsserviços
- **ServiceOrder**: responsável por criar e listar pedidos (`POST /orders`, `GET /orders`).
- **ServicePayment**: responsável por processar pagamentos dos pedidos.

## Fluxo Assíncrono
1. O cliente cria um pedido via ServiceOrder.
2. O ServiceOrder publica uma mensagem no RabbitMQ.
3. O ServicePayment consome a mensagem e processa o pagamento.

```sh
sequenceDiagram
    participant Cliente
    participant ServiceOrder
    participant RabbitMQ
    participant ServicePayment

    Cliente->>ServiceOrder: POST /orders
    ServiceOrder->>RabbitMQ: Publica pedido na fila
    RabbitMQ->>ServicePayment: Entrega mensagem
    ServicePayment->>ServicePayment: Processa pagamento
```
## Como Executar

1. Clonar o repositório
```
git clone https://github.com/fxshelll/microservices-async-demo.git
```

2. Subir os serviços
```
docker compose up --build
```
3. Acessar o RabbitMQ

    Painel: http://localhost:15672

    Usuário: guest

    Senha: guest




## Testes com cURL
```
curl -X POST http://localhost:3001/orders \
     -H "Content-Type: application/json" \
     -d '{"id": 1, "item": "Curso Microsserviços", "valor": 149.90}'
```

Listar pedidos
```
curl http://localhost:3001/orders
```
Listar pagamentos
```
curl http://localhost:3002/payments
```
Considerações

    Os serviços aguardam o RabbitMQ estar pronto antes de iniciar.

    A fila utilizada é chamada orders.

    Os pagamentos são simulados com delay e registrados com timestamp.
