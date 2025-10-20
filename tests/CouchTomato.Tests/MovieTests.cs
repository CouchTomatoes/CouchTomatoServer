using Xunit;
using CouchTomato.Data;
using CouchTomato.Data.Entities;
using Microsoft.EntityFrameworkCore;

namespace CouchTomato.Tests;

public class MovieTests
{
    [Fact]
    public async Task AddMovie_SavesSuccessfully()
    {
        var opts = new DbContextOptionsBuilder<CouchTomatoContext>()
            .UseSqlite("DataSource=:memory:")
            .Options;

        using var ctx = new CouchTomatoContext(opts);
        ctx.Database.OpenConnection();
        ctx.Database.EnsureCreated();

        var movie = new Movie { Title = "Inception", Year = 2010 };
        ctx.Set<Movie>().Add(movie);
        var result = await ctx.SaveChangesAsync();

        Assert.Equal(1, result);
    }
}