const express = require('express');
const router = express.Router();
const db = require('../db');

// GET /api/app-users  — for manager dropdown
router.get('/app-users', async (req, res) => {
  try {
    const [rows] = await db.query(
      'SELECT id, full_name, email FROM app_users WHERE active_ind = 1 ORDER BY full_name'
    );
    res.json({ success: true, data: rows });
  } catch (err) {
    console.error('GET /api/app-users error:', err);
    res.status(500).json({ success: false, error: err.message });
  }
});

// GET /api/homeowners  — for owner dropdown
router.get('/homeowners', async (req, res) => {
  try {
    const [rows] = await db.query(
      'SELECT id, full_name, email, phone FROM homeowners WHERE active_ind = 1 ORDER BY full_name'
    );
    res.json({ success: true, data: rows });
  } catch (err) {
    console.error('GET /api/homeowners error:', err);
    res.status(500).json({ success: false, error: err.message });
  }
});

// GET /api/organizations  — for org_id lookup
router.get('/organizations', async (req, res) => {
  try {
    const [rows] = await db.query(
      'SELECT id, name, slug FROM organizations WHERE active_ind = 1 ORDER BY name'
    );
    res.json({ success: true, data: rows });
  } catch (err) {
    console.error('GET /api/organizations error:', err);
    res.status(500).json({ success: false, error: err.message });
  }
});

module.exports = router;
