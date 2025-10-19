using Xunit;
using CouchTomato.Data;
using Microsoft.EntityFrameworkCore;

namespace CouchTomato.Tests
{
    public class DataTests
    {
        [Fact]
        public void Context_CreatesDatabase()
        {
            var options = new DbContextOptionsBuilder<CouchTomatoContext>()
                .UseSqlite("Data Source=:memory:")
                .Options;

            using var ctx = new CouchTomatoContext(options);
            ctx.Database.OpenConnection();
            ctx.Database.EnsureCreated();

            Assert.True(ctx.Database.CanConnect());
        }
    }
}
