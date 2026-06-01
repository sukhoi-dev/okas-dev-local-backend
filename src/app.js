require('dotenv').config();
const express = require('express');
const cors = require('cors');

const projectsRouter = require('./routes/projects');
const usersRouter = require('./routes/users');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'okas-cloud-backend', ts: new Date().toISOString() });
});

app.use('/api/projects', projectsRouter);
app.use('/api', usersRouter);

app.listen(PORT, () => {
  console.log(`okas-cloud-backend listening on port ${PORT}`);
});
