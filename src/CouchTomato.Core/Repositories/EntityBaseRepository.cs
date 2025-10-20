using Microsoft.EntityFrameworkCore;
using System.Linq.Expressions;
using CouchTomato.Core.Interfaces;
using CouchTomato.Data;
using CouchTomato.Data.Entities;

namespace CouchTomato.Core.Repositories;

public class EntityBaseRepository<T> : IEntityBaseRepository<T> where T : class, IEntityBase
{
    protected readonly CouchTomatoContext _db;

    public EntityBaseRepository(CouchTomatoContext db) => _db = db;

    public IQueryable<T> All => _db.Set<T>().Where(x => !x.IsDeleted);

    public async Task<T> AddAsync(T entity)
    {
        entity.IsDeleted = false;
        entity.CreatedDate = entity.ModifiedDate = DateTime.UtcNow;
        entity.CreatedDateUnix = entity.ModifiedDateUnix = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
        await _db.Set<T>().AddAsync(entity);
        await _db.SaveChangesAsync();
        return entity;
    }

    public async Task<List<T>> GetAllAsync() => await All.ToListAsync();

    public async Task<T?> GetByIdAsync(Guid id) =>
        await All.FirstOrDefaultAsync(x => x.ID == id);

    public void SoftDelete(T entity)
    {
        entity.IsDeleted = true;
        entity.ModifiedDate = DateTime.UtcNow;
        _db.Entry(entity).State = EntityState.Modified;
    }

    public async Task SaveAsync() => await _db.SaveChangesAsync();
}
