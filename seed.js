const mongoose = require('mongoose');
const User = require('./models/User');
require('dotenv').config();

async function seedUsers() {
  try {
    await mongoose.connect(process.env.MONGODB_URI);
    console.log('Connected to MongoDB');

    const dummyUsers = [
      {
        firstName: 'John',
        lastName: 'Doe',
        email: 'john.doe@example.com',
        password: 'password123',
        city: 'New York',
        state: 'NY',
        isVerified: true
      },
      {
        firstName: 'Jane',
        lastName: 'Smith',
        email: 'jane.smith@example.com',
        password: 'password123',
        city: 'Los Angeles',
        state: 'CA',
        isVerified: true
      },
      {
        firstName: 'Alice',
        lastName: 'Johnson',
        email: 'alice.johnson@example.com',
        password: 'password123',
        city: 'Chicago',
        state: 'IL',
        isVerified: false
      }
    ];

    for (const userData of dummyUsers) {
      const existingUser = await User.findOne({ email: userData.email });
      if (!existingUser) {
        const user = new User(userData);
        await user.save();
        console.log(`Created user: ${userData.email}`);
      } else {
        console.log(`User already exists: ${userData.email}`);
      }
    }

    console.log('Seeding completed');
  } catch (error) {
    console.error('Seeding failed:', error);
  } finally {
    mongoose.connection.close();
  }
}

seedUsers();