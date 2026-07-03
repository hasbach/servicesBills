import React, { useState } from 'react';
import { Box, Typography, TextField, Button, Paper, CircularProgress } from '@mui/material';
import { useAppContext } from '../context/AppContext.js';

const RegisterView = ({ onSwitchToLogin }) => {
    const { apiService, setSnackbar } = useAppContext();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleRegister = async (e) => {
        e.preventDefault();
        if (!username || !password) {
            setSnackbar({ open: true, message: 'Please enter username and password.', severity: 'warning' });
            return;
        }
        setLoading(true);
        try {
            const response = await apiService.register({ username, password });
            setSnackbar({ open: true, message: response.data.msg, severity: 'success' });
            onSwitchToLogin(); // Switch to login view after successful registration
        } catch (error) {
            setSnackbar({ open: true, message: error.response?.data?.msg || 'Registration failed.', severity: 'error' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
            <Paper component="form" onSubmit={handleRegister} sx={{ p: 4, width: '100%', maxWidth: '400px', borderRadius: '16px' }}>
                <Typography variant="h4" sx={{ mb: 3, textAlign: 'center', fontWeight: 'bold' }}>Register</Typography>
                <TextField
                    fullWidth
                    label="Username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    margin="normal"
                />
                <TextField
                    fullWidth
                    label="Password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    margin="normal"
                />
                <Button type="submit" variant="contained" fullWidth sx={{ mt: 2, py: 1.5 }} disabled={loading}>
                    {loading ? <CircularProgress size={24} /> : 'Register'}
                </Button>
                <Button fullWidth sx={{ mt: 2 }} onClick={onSwitchToLogin}>
                    Already have an account? Login
                </Button>
            </Paper>
        </Box>
    );
};

export default RegisterView;
