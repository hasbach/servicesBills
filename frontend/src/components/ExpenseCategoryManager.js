import React, { useState, useEffect, useCallback } from 'react';
import { Box, Typography, Button, TextField, List, ListItem, ListItemText, IconButton, Paper } from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, Save as SaveIcon, Cancel as CancelIcon } from '@mui/icons-material';
import { useAppContext } from '../context/AppContext.js';

const ExpenseCategoryManager = () => {
    const { apiService, setSnackbar } = useAppContext();
    const [categories, setCategories] = useState([]);
    const [newCategoryName, setNewCategoryName] = useState('');
    const [editingId, setEditingId] = useState(null);
    const [editingName, setEditingName] = useState('');

    const fetchCategories = useCallback(async () => {
        try {
            const response = await apiService.fetchExpenseCategories();
            setCategories(response.data);
        } catch (error) {
            setSnackbar({ open: true, message: 'Failed to fetch categories.', severity: 'error' });
        }
    }, [apiService, setSnackbar]);

    useEffect(() => {
        fetchCategories();
    }, [fetchCategories]);

    const handleAddCategory = async () => {
        if (!newCategoryName.trim()) {
            setSnackbar({ open: true, message: 'Category name cannot be empty.', severity: 'warning' });
            return;
        }
        try {
            await apiService.addExpenseCategory({ name: newCategoryName });
            setSnackbar({ open: true, message: 'Category added successfully!', severity: 'success' });
            setNewCategoryName('');
            fetchCategories();
        } catch (error) {
            setSnackbar({ open: true, message: error.response?.data?.error || 'Failed to add category.', severity: 'error' });
        }
    };

    const handleDeleteCategory = async (categoryId) => {
        if (window.confirm('Are you sure you want to delete this category?')) {
            try {
                await apiService.deleteExpenseCategory(categoryId);
                setSnackbar({ open: true, message: 'Category deleted successfully!', severity: 'success' });
                fetchCategories();
            } catch (error) {
                setSnackbar({ open: true, message: error.response?.data?.error || 'Failed to delete category.', severity: 'error' });
            }
        }
    };

    const handleEdit = (category) => {
        setEditingId(category.id);
        setEditingName(category.name);
    };

    const handleCancelEdit = () => {
        setEditingId(null);
        setEditingName('');
    };

    const handleSaveEdit = async (categoryId) => {
        if (!editingName.trim()) {
            setSnackbar({ open: true, message: 'Category name cannot be empty.', severity: 'warning' });
            return;
        }
        try {
            await apiService.updateExpenseCategory(categoryId, { name: editingName });
            setSnackbar({ open: true, message: 'Category updated successfully!', severity: 'success' });
            handleCancelEdit();
            fetchCategories();
        } catch (error) {
            setSnackbar({ open: true, message: error.response?.data?.error || 'Failed to update category.', severity: 'error' });
        }
    };

    return (
        <Paper sx={{ p: 3, mt: 4 }}>
            <Typography variant="h6" gutterBottom>Manage Expense Categories</Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <TextField
                    label="New Category Name"
                    value={newCategoryName}
                    onChange={(e) => setNewCategoryName(e.target.value)}
                    size="small"
                    sx={{ flexGrow: 1 }}
                />
                <Button variant="contained" onClick={handleAddCategory} startIcon={<AddIcon />}>Add</Button>
            </Box>
            <List>
                {categories.map((category) => (
                    <ListItem key={category.id} secondaryAction={
                        editingId === category.id ? (
                            <>
                                <IconButton edge="end" onClick={() => handleSaveEdit(category.id)}><SaveIcon color="primary" /></IconButton>
                                <IconButton edge="end" onClick={handleCancelEdit}><CancelIcon /></IconButton>
                            </>
                        ) : (
                            <>
                                <IconButton edge="end" onClick={() => handleEdit(category)}><EditIcon /></IconButton>
                                <IconButton edge="end" onClick={() => handleDeleteCategory(category.id)}><DeleteIcon color="error" /></IconButton>
                            </>
                        )
                    }>
                        {editingId === category.id ? (
                            <TextField
                                value={editingName}
                                onChange={(e) => setEditingName(e.target.value)}
                                size="small"
                                autoFocus
                            />
                        ) : (
                            <ListItemText primary={category.name} />
                        )}
                    </ListItem>
                ))}
            </List>
        </Paper>
    );
};

export default ExpenseCategoryManager;
