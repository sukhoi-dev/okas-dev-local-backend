const express = require('express');
const router = express.Router();
const db = require('../db');

// GET /api/projects
router.get('/', async (req, res) => {
  try {
    const [rows] = await db.query(`
      SELECT
        p.id,
        p.name,
        p.serial_number,
        p.project_type,
        p.address,
        p.city,
        p.state,
        p.installed_at,
        p.status,
        h.full_name  AS owner_name,
        h.email      AS owner_email,
        h.phone      AS owner_phone,
        u.full_name  AS manager_name,
        ps.status    AS subscription_status
      FROM projects p
      LEFT JOIN project_owners po ON po.project_id = p.id AND po.is_primary = 1 AND po.active_ind = 1
      LEFT JOIN homeowners h      ON h.id = po.homeowner_id
      LEFT JOIN app_users u       ON u.id = p.project_manager_id
      LEFT JOIN project_subscriptions ps ON ps.project_id = p.id
      WHERE p.active_ind = 1
      ORDER BY p.created_at DESC
    `);
    res.json({ success: true, data: rows });
  } catch (err) {
    console.error('GET /api/projects error:', err);
    res.status(500).json({ success: false, error: err.message });
  }
});

// POST /api/projects
// Body: { name, serial_number, project_type, address, city, state, pincode, notes,
//         project_manager_id, organization_id,
//         primary_contact: { full_name, email, phone } }
router.post('/', async (req, res) => {
  const {
    name,
    serial_number,
    project_type = 'residential',
    address,
    city,
    state,
    pincode,
    notes,
    project_manager_id,
    organization_id,
    primary_contact,
  } = req.body;

  if (!name || !organization_id) {
    return res.status(400).json({ success: false, error: 'name and organization_id are required' });
  }

  const conn = await db.getConnection();
  try {
    await conn.beginTransaction();

    // 1. Insert project
    const [projResult] = await conn.query(
      `INSERT INTO projects
         (organization_id, project_manager_id, name, serial_number, project_type,
          address, city, state, pincode, notes, installed_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(3))`,
      [
        organization_id,
        project_manager_id || null,
        name,
        serial_number || null,
        project_type,
        address || null,
        city || null,
        state || null,
        pincode || null,
        notes || null,
      ]
    );
    const projectId = projResult.insertId;

    // 2. Create / link homeowner as primary contact
    if (primary_contact?.email) {
      let homeownerId;
      const [existing] = await conn.query(
        'SELECT id FROM homeowners WHERE email = ?',
        [primary_contact.email]
      );
      if (existing.length > 0) {
        homeownerId = existing[0].id;
      } else {
        const [hwResult] = await conn.query(
          'INSERT INTO homeowners (full_name, email, phone) VALUES (?, ?, ?)',
          [primary_contact.full_name || primary_contact.email, primary_contact.email, primary_contact.phone || null]
        );
        homeownerId = hwResult.insertId;
      }
      await conn.query(
        'INSERT INTO project_owners (project_id, homeowner_id, is_primary) VALUES (?, ?, 1)',
        [projectId, homeownerId]
      );
    }

    await conn.commit();

    // Return the created project (re-fetch with joins)
    const [created] = await conn.query(
      `SELECT p.id, p.name, p.serial_number, p.project_type, p.address, p.city,
              p.installed_at, p.status,
              h.full_name AS owner_name, h.email AS owner_email, h.phone AS owner_phone,
              u.full_name AS manager_name
       FROM projects p
       LEFT JOIN project_owners po ON po.project_id = p.id AND po.is_primary = 1
       LEFT JOIN homeowners h      ON h.id = po.homeowner_id
       LEFT JOIN app_users u       ON u.id = p.project_manager_id
       WHERE p.id = ?`,
      [projectId]
    );

    res.status(201).json({ success: true, data: created[0] });
  } catch (err) {
    await conn.rollback();
    console.error('POST /api/projects error:', err);
    res.status(500).json({ success: false, error: err.message });
  } finally {
    conn.release();
  }
});

module.exports = router;
