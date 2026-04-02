const express = require('express');
const mongoose = require('mongoose');
const Complaint = require('../models/Complaint');
const Vote = require('../models/Vote');
const User = require('../models/User');
const auth = require('../middleware/auth');

const router = express.Router();

// Get all complaints (with user vote status)
router.get('/', async (req, res) => {
  try {
    const complaints = await Complaint.find()
      .populate('author', 'firstName lastName isVerified')
      .sort({ createdAt: -1 });

    // Get current user's votes if authenticated
    let userVotes = {};
    const token = req.header('Authorization')?.replace('Bearer ', '');
    if (token) {
      try {
        const jwt = require('jsonwebtoken');
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        const votes = await Vote.find({ user: decoded.userId });
        votes.forEach(vote => {
          userVotes[vote.complaint.toString()] = vote.voteType;
        });
      } catch (e) {}
    }

    const formattedComplaints = complaints.map(c => ({
      id: c._id,
      user: `${c.author.firstName} ${c.author.lastName}`,
      init: (c.author.firstName[0] + c.author.lastName[0]).toUpperCase(),
      verified: c.author.isVerified,
      time: getRelativeTime(c.createdAt),
      cat: c.category,
      title: c.title,
      body: c.description,
      location: `${c.location.city}, ${c.location.state}`,
      tags: c.tags,
      up: c.upvotes,
      dn: c.downvotes,
      comments: c.commentCount,
      status: c.status,
      urgency: c.urgency,
      proofs: c.proofs.length ? c.proofs : ['📎'],
      viral: c.isViral,
      pinned: c.isPinned,
      authResp: c.authResponse,
      uv: userVotes[c._id.toString()] || ''
    }));

    res.json(formattedComplaints);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to fetch complaints' });
  }
});

// Create complaint
router.post('/', auth, async (req, res) => {
  try {
    const { title, category, description, city, state, tags, urgency } = req.body;

    const complaint = new Complaint({
      title,
      description,
      category,
      urgency,
      location: { city, state },
      tags: tags || [],
      proofs: ['📷', '📹'],
      author: req.userId
    });

    await complaint.save();

    // Auto-mark as viral if high upvotes? Not needed now
    const populated = await complaint.populate('author', 'firstName lastName isVerified');

    res.status(201).json({
      id: complaint._id,
      user: `${populated.author.firstName} ${populated.author.lastName}`,
      init: (populated.author.firstName[0] + populated.author.lastName[0]).toUpperCase(),
      verified: populated.author.isVerified,
      time: 'Just now',
      cat: complaint.category,
      title: complaint.title,
      body: complaint.description,
      location: `${complaint.location.city}, ${complaint.location.state}`,
      tags: complaint.tags,
      up: 0,
      dn: 0,
      comments: 0,
      status: complaint.status,
      urgency: complaint.urgency,
      proofs: complaint.proofs,
      viral: false,
      pinned: false,
      authResp: '',
      uv: ''
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to create complaint' });
  }
});

// Vote on complaint
router.post('/:id/vote', auth, async (req, res) => {
  try {
    const { id } = req.params;
    const { vote } = req.body; // 'up' or 'down'

    if (!['up', 'down'].includes(vote)) {
      return res.status(400).json({ error: 'Invalid vote type' });
    }

    const complaint = await Complaint.findById(id);
    if (!complaint) {
      return res.status(404).json({ error: 'Complaint not found' });
    }

    // Check existing vote
    let existingVote = await Vote.findOne({ user: req.userId, complaint: id });

    if (existingVote) {
      // Remove old vote counts
      if (existingVote.voteType === 'up') complaint.upvotes--;
      else complaint.downvotes--;

      // If same vote type, remove vote (undo)
      if (existingVote.voteType === vote) {
        await existingVote.deleteOne();
      } else {
        // Change vote
        existingVote.voteType = vote;
        await existingVote.save();
        if (vote === 'up') complaint.upvotes++;
        else complaint.downvotes++;
      }
    } else {
      // New vote
      await Vote.create({ user: req.userId, complaint: id, voteType: vote });
      if (vote === 'up') complaint.upvotes++;
      else complaint.downvotes++;
    }

    await complaint.save();

    // Auto-mark as viral if upvotes > 1000
    if (complaint.upvotes > 1000 && !complaint.isViral) {
      complaint.isViral = true;
      await complaint.save();
    }

    res.json({
      upvotes: complaint.upvotes,
      downvotes: complaint.downvotes,
      userVote: existingVote?.voteType === vote ? '' : vote
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Failed to process vote' });
  }
});

// Helper function for relative time
function getRelativeTime(date) {
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

module.exports = router;