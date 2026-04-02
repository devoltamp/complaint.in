const express = require('express');
const jwt = require('jsonwebtoken');
const User = require('../models/User');
const auth = require('../middleware/auth');

const router = express.Router();

// Register
router.post('/register', async (req, res) => {
  try {
    const { first_name, last_name, email, password, city, state } = req.body;
    
    // Check if user exists
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({ error: 'Email already registered' });
    }

    // Create user
    const user = new User({
      firstName: first_name,
      lastName: last_name,
      email,
      password,
      city,
      state
    });

    await user.save();

    // Generate token
    const token = jwt.sign({ userId: user._id }, process.env.JWT_SECRET, { expiresIn: '7d' });

    res.status(201).json({
      token,
      user: {
        id: user._id,
        name: `${user.firstName} ${user.lastName}`,
        initials: user.initials,
        email: user.email,
        city: user.city,
        state: user.state,
        verified: user.isVerified
      }
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Registration failed' });
  }
});

// Login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    const user = await User.findOne({ email });
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = jwt.sign({ userId: user._id }, process.env.JWT_SECRET, { expiresIn: '7d' });

    res.json({
      token,
      user: {
        id: user._id,
        name: `${user.firstName} ${user.lastName}`,
        initials: user.initials,
        email: user.email,
        city: user.city,
        state: user.state,
        verified: user.isVerified
      }
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Login failed' });
  }
});

// Get current user
router.get('/me', auth, async (req, res) => {
  res.json({
    id: req.user._id,
    name: `${req.user.firstName} ${req.user.lastName}`,
    initials: req.user.initials,
    email: req.user.email,
    city: req.user.city,
    state: req.user.state,
    verified: req.user.isVerified
  });
});

module.exports = router;